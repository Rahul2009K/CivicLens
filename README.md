# CivicLens

CivicLens translates U.S. congressional bills into plain English using Claude AI, making legislation accessible to high school students and anyone without a civics or legal background.

## What it does

1. Fetches recent bills from the Congress.gov API
2. Sends each bill's title, official summary, and latest action to Claude
3. Returns a structured JSON summary with a plain-English title, 2–3 sentence explanation, key provisions, who is affected, topic tags, and current status

## Project structure

```
fetch_bills.py      — pulls bills from Congress.gov
summarize_bill.py   — sends bill data to Claude, returns plain-English JSON
test_pipeline.py    — end-to-end test of the full pipeline
test_results.json   — sample output from a pipeline test run
```

## Setup

1. **Clone the repo and create a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install anthropic requests python-dotenv
   ```

2. **Create a `.env` file** in the project root with your API keys:

   ```
   CONGRESS_API_KEY=your_congress_api_key_here
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

   - Get a Congress.gov API key at [api.congress.gov](https://api.congress.gov/sign-up/)
   - Get an Anthropic API key at [console.anthropic.com](https://console.anthropic.com/)

## Usage

**Fetch and print recent bills:**
```bash
python fetch_bills.py
```

**Test the summarization pipeline on a sample bill:**
```bash
python summarize_bill.py
```

**Run the full end-to-end pipeline test:**
```bash
python test_pipeline.py
```

## Output format

Each bill is summarized as a JSON object:

```json
{
  "plain_title": "Short title a teenager would understand",
  "plain_summary": "2-3 sentences explaining what the bill actually does...",
  "key_provisions": ["provision 1", "provision 2", "provision 3"],
  "who_it_affects": "Which groups of people this bill would impact and how.",
  "topics": ["Education", "Economy"],
  "status_plain_english": "Where this bill is in the process right now."
}
```

## Model

Summarization uses `claude-sonnet-4-6` via the Anthropic Python SDK.
