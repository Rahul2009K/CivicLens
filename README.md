# CivicLens (data pipeline + API)

CivicLens explains the 100 newest bills in the U.S. Congress in plain English, for high school students and anyone without a civics or legal background.

**Live site:** https://civiclens-frontend-gilt.vercel.app · **Website code:** [civiclens-frontend](https://github.com/Rahul2009K/civiclens-frontend)

This repo fetches bills from Congress.gov, has Claude rewrite each one in plain English, and serves the results to the website.

## How it works

1. **Fetch** the newest bills of the 119th Congress from the [Congress.gov API](https://api.congress.gov/), skipping placeholder bill numbers reserved for House leadership.
2. **Gather sources** for each bill: the official summary from the Congressional Research Service when one exists, the full bill text (trimmed at about 10k tokens), the latest action, and details like the sponsor, introduced date and cosponsor count.
3. **Summarize** with Claude (`claude-opus-5-5`) using **structured outputs**, so every response is guaranteed to match the JSON schema. The prompt tells Claude to stay neutral, not to invent details, and to write for a high schooler.
4. **Label the source** of every summary (`official_summary`, `bill_text` or `title_only`) so the site can tell readers what the summary was based on.
5. **Cache** everything in `bills_cache.json` and copy it to the website as a snapshot. The Flask API serves the cache instantly; no Claude calls happen when someone visits the site.

In the current batch, 96 of 100 summaries are based on the official summary or the full bill text.

## Files

```
generate_cache.py   runs the whole pipeline (parallel), writes bills_cache.json + the site snapshot
fetch_bills.py      Congress.gov helpers: bill list, details, official summary, full text
summarize_bill.py   Claude call with a JSON schema, refusal and error handling
app.py              Flask API: GET /bills, GET /health
tests_app.py        unit tests (no keys or network needed)
render.yaml         Render deployment (gunicorn)
test_pipeline.py    manual end-to-end check on 10 live bills (uses API credits)
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file:

```
CONGRESS_API_KEY=your_congress_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

Keys: [api.congress.gov/sign-up](https://api.congress.gov/sign-up/) and [console.anthropic.com](https://console.anthropic.com/).

## Usage

```bash
python generate_cache.py        # refresh the 100 bills (Congress.gov + Claude, ~5 minutes)
python app.py                   # API at http://localhost:5000/bills
python -m unittest tests_app    # tests
python summarize_bill.py        # try the summarizer on one sample bill
```

After refreshing, commit `bills_cache.json` here and `public/bills.json` in the website repo so both deployments update.

## Output format

```json
{
  "id": "119-S-5533",
  "plain_title": "No Taxes on AmeriCorps Education Awards",
  "plain_summary": "2-3 sentences, no jargon",
  "key_provisions": ["...", "..."],
  "who_it_affects": "one sentence",
  "why_it_matters": "one sentence connecting it to a young person's life",
  "topics": ["Education", "Economy"],
  "status_plain_english": "where the bill stands, in plain English",
  "source": "bill_text",
  "sponsor": { "name": "Sen. Bennet, Michael F. [D-CO]", "party": "D", "state": "CO" },
  "introduced_date": "2026-09-24",
  "latest_action_date": "2026-09-24",
  "latest_action_text": "Read twice and referred to the Committee on Finance.",
  "cosponsor_count": 7
}
```

## Deployment

The API runs on Render's free tier from `render.yaml` (New → Blueprint → this repo). The free tier sleeps when idle; the website ships its own snapshot of the bills, so visitors never wait on a cold start.
