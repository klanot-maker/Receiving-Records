"""Invoice / purchase-order photo -> structured receiving-record rows, via Google Gemini vision."""
import json
import os

from google import genai
from google.genai import types

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "supplier_name": {
            "type": "STRING",
            "description": "Supplier / vendor name on the document (invoice issuer, or the "
            "'Supplier' column value on a warehouse request line).",
        },
        "receiving_date": {
            "type": "STRING",
            "description": "Date the goods were received, in M/D/YYYY form. Prefer a "
            "handwritten receiving-date stamp/note over the printed invoice date. "
            "Empty string if not shown.",
        },
        "receiving_time": {
            "type": "STRING",
            "description": "Time the goods were received (e.g. '10:20 AM'), from a "
            "handwritten note/stamp if present. Empty string if not shown.",
        },
        "items": {
            "type": "ARRAY",
            "description": "One entry per distinct product/line item on the document.",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "product_name": {"type": "STRING", "description": "Product name/description."},
                    "brand": {
                        "type": "STRING",
                        "description": "Brand name if shown separately from the product "
                        "name (e.g. supplier/manufacturer brand). Empty string if not shown.",
                    },
                    "qty": {
                        "type": "STRING",
                        "description": "Quantity received, including unit if shown (e.g. '12 Tub', '60 Kg').",
                    },
                    "product_temp": {
                        "type": "STRING",
                        "description": "Product temperature at receiving if recorded (e.g. '3.8C'). "
                        "Empty string if not shown.",
                    },
                    "product_date": {
                        "type": "STRING",
                        "description": "Production date of the product if shown. Empty string if not shown.",
                    },
                    "expiry_date": {
                        "type": "STRING",
                        "description": "Expiry / best-before date of the product if shown. "
                        "Empty string if not shown.",
                    },
                },
                "required": [
                    "product_name",
                    "brand",
                    "qty",
                    "product_temp",
                    "product_date",
                    "expiry_date",
                ],
            },
        },
    },
    "required": ["supplier_name", "receiving_date", "receiving_time", "items"],
}

INSTRUCTIONS = (
    "You are reading a photo of a supplier invoice, purchase order, or warehouse "
    "receiving sheet for a food business. Extract every distinct product line so it "
    "can be logged into a Daily Goods Receiving Record. Read both printed text and "
    "any handwritten notes, stamps, or annotations (e.g. a 'RECEIVED' stamp with a "
    "date, or handwritten temperature/date notes next to a line item) — handwritten "
    "receiving date/time/temperature is often more relevant than the printed invoice "
    "date. If multiple photos are provided, treat them as pages of the same delivery "
    "and combine their line items into one list. If a field genuinely is not present "
    "anywhere in the images, return an empty string for it rather than guessing."
)


def _get_client() -> genai.Client:
    if os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").lower() == "true":
        return genai.Client(
            vertexai=True,
            project=os.environ["GOOGLE_CLOUD_PROJECT"],
            location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
        )

    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Set GOOGLE_API_KEY (a Gemini API key from https://aistudio.google.com/apikey) "
            "in the environment, or set GOOGLE_GENAI_USE_VERTEXAI=true plus "
            "GOOGLE_CLOUD_PROJECT to use Vertex AI instead."
        )
    return genai.Client(api_key=api_key)


def extract_rows(images: list[tuple[bytes, str]]) -> list[dict]:
    """images: list of (raw_bytes, media_type). Returns a list of row dicts matching
    sheets.COLUMNS (receiving_date, receiving_time, supplier_name, product_name, brand,
    qty, product_temp, product_date, expiry_date), one per product line found."""
    client = _get_client()

    parts = [types.Part.from_bytes(data=data, mime_type=media_type) for data, media_type in images]
    parts.append(types.Part.from_text(text=INSTRUCTIONS))

    response = client.models.generate_content(
        model=MODEL,
        contents=[types.Content(role="user", parts=parts)],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SCHEMA,
        ),
    )

    parsed = json.loads(response.text)

    rows = []
    for item in parsed.get("items", []):
        rows.append(
            {
                "receiving_date": parsed.get("receiving_date", ""),
                "receiving_time": parsed.get("receiving_time", ""),
                "supplier_name": parsed.get("supplier_name", ""),
                "product_name": item.get("product_name", ""),
                "brand": item.get("brand", ""),
                "qty": item.get("qty", ""),
                "product_temp": item.get("product_temp", ""),
                "product_date": item.get("product_date", ""),
                "expiry_date": item.get("expiry_date", ""),
            }
        )
    return rows
