"""Invoice / purchase-order photo -> structured receiving-record rows, via Claude vision."""
import base64
import json
import os

import anthropic

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8")

SCHEMA = {
    "type": "object",
    "properties": {
        "supplier_name": {
            "type": "string",
            "description": "Supplier / vendor name on the document (invoice issuer, or the "
            "'Supplier' column value on a warehouse request line).",
        },
        "receiving_date": {
            "type": "string",
            "description": "Date the goods were received, in M/D/YYYY form. Prefer a "
            "handwritten receiving-date stamp/note over the printed invoice date. "
            "Empty string if not shown.",
        },
        "receiving_time": {
            "type": "string",
            "description": "Time the goods were received (e.g. '10:20 AM'), from a "
            "handwritten note/stamp if present. Empty string if not shown.",
        },
        "items": {
            "type": "array",
            "description": "One entry per distinct product/line item on the document.",
            "items": {
                "type": "object",
                "properties": {
                    "product_name": {"type": "string", "description": "Product name/description."},
                    "brand": {
                        "type": "string",
                        "description": "Brand name if shown separately from the product "
                        "name (e.g. supplier/manufacturer brand). Empty string if not shown.",
                    },
                    "qty": {
                        "type": "string",
                        "description": "Quantity received, including unit if shown (e.g. '12 Tub', '60 Kg').",
                    },
                    "product_temp": {
                        "type": "string",
                        "description": "Product temperature at receiving if recorded (e.g. '3.8C'). "
                        "Empty string if not shown.",
                    },
                    "product_date": {
                        "type": "string",
                        "description": "Production date of the product if shown. Empty string if not shown.",
                    },
                    "expiry_date": {
                        "type": "string",
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
                "additionalProperties": False,
            },
        },
    },
    "required": ["supplier_name", "receiving_date", "receiving_time", "items"],
    "additionalProperties": False,
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


def _image_block(image_bytes: bytes, media_type: str) -> dict:
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": base64.standard_b64encode(image_bytes).decode("utf-8"),
        },
    }


def extract_rows(images: list[tuple[bytes, str]]) -> list[dict]:
    """images: list of (raw_bytes, media_type). Returns a list of row dicts matching
    sheets.COLUMNS (receiving_date, receiving_time, supplier_name, product_name, brand,
    qty, product_temp, product_date, expiry_date), one per product line found."""
    client = anthropic.Anthropic()

    content = [_image_block(data, media_type) for data, media_type in images]
    content.append({"type": "text", "text": INSTRUCTIONS})

    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[{"role": "user", "content": content}],
    )

    text = next(block.text for block in response.content if block.type == "text")
    parsed = json.loads(text)

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
