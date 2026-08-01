# Cost Analysis Slack Report

Google Apps Script bound to the "Summary" tab of the cost analysis
spreadsheet. `sendCostAnalysisReport()` builds a MoM cost/wastage summary
and posts it to Slack via an incoming webhook, on a daily 8:00 AM GST
trigger.

## Fixing "Exception: DNS error: http://PASTE_SLACK_WEBHOOK_URL_HERE"

This error means the script tried to POST to the literal placeholder text
instead of a real Slack webhook URL — the `SLACK_WEBHOOK_URL` Script
Property was never set (or the webhook was hardcoded as
`PASTE_SLACK_WEBHOOK_URL_HERE` directly in the deployed script).

The webhook URL is a secret and must **never** be committed to this repo.
Set it directly in the Apps Script project instead:

1. Open the Apps Script project bound to the spreadsheet.
2. **Project Settings** (gear icon) → **Script Properties** → **Add script
   property**.
3. Property: `SLACK_WEBHOOK_URL`. Value: your real
   `https://hooks.slack.com/services/...` webhook URL.
4. Save, then re-run `sendCostAnalysisReport` (or wait for the daily
   trigger) — `postToSlack` reads the URL from
   `PropertiesService.getScriptProperties()` at call time, so no code
   change or redeploy is needed.

Alternatively, run `setSlackWebhookUrl()` once from the script editor with
the real URL pasted into that function, then delete the URL from the
source again so it's never saved back to this repo.

## Deploying this file

Copy `CostAnalysisReport.gs` into the Apps Script project bound to the
spreadsheet (or push it there with `clasp`). It's tracked here for version
control / review; the actual runtime secret lives only in that project's
Script Properties.
