# Receiving Record Capture App

A small web app: take a photo of an invoice or purchase order, and Claude
extracts the product lines (supplier, product, brand, qty, temp, production
date, expiry/BB date) so you can review and save them straight into the
**Daily Goods Receiving Record** Google Sheet.

Sheet: https://docs.google.com/spreadsheets/d/1R_qUspQW-elqBi3UGEXt5gNLuy2qkVrlyRnhkaEveKI/edit#gid=0

Columns filled: A Receiving date · B Receiving time · C Supplier name ·
D Product name · E Brand · F Qty · G Product temp · H Product date ·
I Expiry / Best-before date.

## How it works

1. Open the page on your phone, take a photo (or several pages) of the
   invoice/PO.
2. The app sends the photo(s) to Claude, which reads printed text *and*
   handwritten notes/stamps (receiving date, temperature, etc.) and returns
   one row per product line.
3. You review/edit the extracted rows in an editable table (OCR isn't
   perfect — check quantities and dates before saving).
4. Tap **Save to sheet** — the rows are appended to the Google Sheet via the
   Sheets API.

## One-time setup

### 1. Anthropic API key

Get a key at https://console.anthropic.com and set it as `ANTHROPIC_API_KEY`.

### 2. Google service account (so the app can write to the Sheet)

1. In Google Cloud Console, create (or reuse) a project, then enable the
   **Google Sheets API**.
2. Create a **Service Account**, then create a JSON key for it and download
   it — save it as `service-account.json` next to `app.py` (or paste its
   contents into `GOOGLE_SERVICE_ACCOUNT_JSON`).
3. Open the service account's JSON file and copy its `client_email`
   (looks like `something@project.iam.gserviceaccount.com`).
4. Open the Google Sheet, click **Share**, and share it with that email
   address with **Editor** access.

### 3. Configure the app

```bash
cd app
cp .env.example .env
# edit .env: set ANTHROPIC_API_KEY, GOOGLE_SERVICE_ACCOUNT_FILE, SHEET_ID, SHEET_NAME
```

`SHEET_ID` is already set to the sheet from the task; `SHEET_NAME` is the tab
name (the gid=0 tab — usually `Sheet1`, check the tab label at the bottom of
the spreadsheet and adjust if different).

### 4. Install & run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000` (or your machine's LAN IP from a phone on the
same network) and start capturing.

For real phone use over the internet, deploy this behind HTTPS (e.g. a small
VM, Render, Fly.io, Cloud Run) — camera capture (`capture="environment"`)
requires HTTPS on most mobile browsers except on `localhost`.

## Notes / limitations

- Extraction quality depends on photo clarity — crop tightly, avoid glare,
  and keep handwriting legible.
- Always review the extracted table before saving — OCR can misread
  quantities, dates, or handwriting.
- The app appends new rows; it never edits or deletes existing sheet rows.
