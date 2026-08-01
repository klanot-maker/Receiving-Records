"""Google Sheets helper — appends receiving-record rows to the configured sheet."""
import os

from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Columns A..I in this exact order.
COLUMNS = [
    "receiving_date",
    "receiving_time",
    "supplier_name",
    "product_name",
    "brand",
    "qty",
    "product_temp",
    "product_date",
    "expiry_date",
]


def _get_credentials():
    key_file = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE")
    key_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")

    if key_file:
        return service_account.Credentials.from_service_account_file(
            key_file, scopes=SCOPES
        )
    if key_json:
        import json

        info = json.loads(key_json)
        return service_account.Credentials.from_service_account_info(
            info, scopes=SCOPES
        )
    raise RuntimeError(
        "Set GOOGLE_SERVICE_ACCOUNT_FILE (path to a service account JSON key) "
        "or GOOGLE_SERVICE_ACCOUNT_JSON (the key contents) in the environment."
    )


def _sheets_service():
    creds = _get_credentials()
    return build("sheets", "v4", credentials=creds)


def append_rows(rows):
    """rows: list of dicts keyed by COLUMNS. Appends one sheet row per dict."""
    spreadsheet_id = os.environ["SHEET_ID"]
    sheet_name = os.environ.get("SHEET_NAME", "Sheet1")

    values = [[row.get(col, "") for col in COLUMNS] for row in rows]
    if not values:
        return {"updates": {"updatedRows": 0}}

    service = _sheets_service()
    body = {"values": values}
    result = (
        service.spreadsheets()
        .values()
        .append(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A:I",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body,
        )
        .execute()
    )
    return result
