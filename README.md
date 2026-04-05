# Finance Outreach Generator

Turn messy LinkedIn-style notes into a clean, high-conversion finance networking outreach package.

## What it generates
- `Key Insights` (3 bullets)
- `Firm Insight` (strategy summary or inferred strategy)
- `Subject Line Options` (3 options)
- `Email` (tailored, concise, under 180 words)
- `Possible Email Formats` (if email is unknown)

## Setup
### Option 1: One-command setup
```bash
./setup.sh
source .venv/bin/activate
```

### Option 2: Manual setup
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

## Quick start
From the repo root:

```bash
python finance_outreach_generator.py \
  --name "Alex Chen" \
  --firm "Summit Ridge Partners" \
  --role "Associate, Private Equity" \
  --raw-background "Sources and executes founder-led software buyouts. Previously at Jefferies M&A. Closed 8 transactions; fund size $750m." \
  --firm-info "N/A" \
  --email "Unknown" \
  --major "Finance"
```

## Run as a website app
After setup and virtualenv activation:

```bash
python app.py
```

Then open `http://127.0.0.1:8000` in your browser.  
Use **Generate** for full text output, or **Download CSV Row** for a Google Sheets-ready row file.

## Easier input: JSON file
You can also pass one JSON file instead of a long command.

1) Create `sample_input.json`:

```json
{
  "name": "Jordan Lee",
  "firm": "Apex Capital Partners",
  "role": "Senior Associate, Private Equity",
  "raw_background": "Leads deal execution and underwriting for lower middle-market industrials. Previously at Houlihan Lokey. Closed 12+ transactions and supports a $1.2bn AUM strategy.",
  "firm_info": "control buyouts in industrial and business services with EBITDA $5-25m",
  "email": "Unknown",
  "major": "Finance and Statistics"
}
```

2) Run:

```bash
python finance_outreach_generator.py --input-json sample_input.json
```

## Run tests

```bash
python -m pytest -q
```

## Google Sheets-friendly output
Export directly to CSV so you can paste/import into Google Sheets.

```bash
python finance_outreach_generator.py \
  --input-json sample_input.json \
  --output-format csv \
  --output-path outreach_rows.csv
```

You can then import `outreach_rows.csv` into Sheets. A header-only template is also included at `google_sheets_template.csv`.

## Notes
- If `firm_info` is omitted or `N/A`, the script infers likely strategy from firm and role.
- If `email` is `Unknown`, the script returns likely company email patterns.
- API endpoint available: `POST /api/generate` on port `8000` (JSON input, JSON output).
