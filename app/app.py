"""Web app: photograph an invoice/PO, extract line items with Claude, review, and
push the result straight into the Daily Goods Receiving Record Google Sheet."""
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

from extractor import extract_rows  # noqa: E402  (after load_dotenv)
from sheets import COLUMNS, append_rows  # noqa: E402

app = Flask(__name__)

MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB per photo
ALLOWED_MEDIA_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/extract", methods=["POST"])
def extract():
    files = request.files.getlist("photos")
    if not files:
        return jsonify({"error": "No photos were uploaded."}), 400

    images = []
    for f in files:
        media_type = f.mimetype
        if media_type not in ALLOWED_MEDIA_TYPES:
            return jsonify({"error": f"Unsupported file type: {media_type}"}), 400
        data = f.read()
        if len(data) > MAX_IMAGE_BYTES:
            return jsonify({"error": f"{f.filename} is larger than 10 MB."}), 400
        images.append((data, media_type))

    try:
        rows = extract_rows(images)
    except Exception as exc:  # surfaced to the user for retry, not swallowed
        return jsonify({"error": f"Extraction failed: {exc}"}), 500

    return jsonify({"rows": rows, "columns": COLUMNS})


@app.route("/submit", methods=["POST"])
def submit():
    payload = request.get_json(silent=True) or {}
    rows = payload.get("rows")
    if not rows:
        return jsonify({"error": "No rows to save."}), 400

    try:
        result = append_rows(rows)
    except Exception as exc:
        return jsonify({"error": f"Could not write to the sheet: {exc}"}), 500

    updated = result.get("updates", {}).get("updatedRows", len(rows))
    return jsonify({"saved": updated})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
