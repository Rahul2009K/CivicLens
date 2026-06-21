"""
summarize_bill.py
Takes raw bill text/summary from Congress.gov and uses Claude to produce
a structured, plain-English JSON summary.
"""

import os
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SUMMARIZATION_PROMPT = """You are helping translate U.S. congressional bills into plain English for high school students who have little background in civics or legal language.

Here is the official bill information:

Title: {title}
Official summary: {official_summary}
Latest action: {latest_action}

Produce a JSON object with EXACTLY this structure and nothing else -- no preamble, no markdown formatting, just the raw JSON:

{{
  "plain_title": "a short, clear title a teenager would understand (max 12 words)",
  "plain_summary": "2-3 sentences explaining what this bill actually does, written for someone with zero background in this topic. Avoid legal jargon. Use concrete examples where possible.",
  "key_provisions": ["short phrase describing provision 1", "short phrase describing provision 2", "short phrase describing provision 3"],
  "who_it_affects": "one sentence describing which groups of people this bill would impact and how",
  "topics": ["pick 1-3 from: Education, Immigration, Healthcare, Climate, Economy, Civil Rights, Criminal Justice, Technology, Foreign Policy, Other"],
  "status_plain_english": "one sentence translating the latest legislative action into plain English (e.g. 'This bill was just introduced and hasn't been voted on yet')"
}}

Respond with ONLY the JSON object, no other text."""


def summarize_bill(title, official_summary, latest_action):
    """Call Claude to transform raw bill data into a structured plain-English summary."""
    prompt = SUMMARIZATION_PROMPT.format(
        title=title,
        official_summary=official_summary or "No official summary available yet.",
        latest_action=latest_action or "No action recorded yet.",
    )

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = message.content[0].text.strip()

    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as e:
        print(f"WARNING: Could not parse Claude's response as JSON: {e}")
        print(f"Raw response was:\n{raw_text}")
        return None


if __name__ == "__main__":
    test_title = "A bill to require schools to teach personal financial literacy"
    test_summary = "This bill requires public secondary schools to include a personal financial literacy course as part of the standard curriculum, covering budgeting, credit, taxes, and saving for retirement."
    test_action = "Referred to the Committee on Education and the Workforce."

    print("Testing summarization pipeline...\n")
    result = summarize_bill(test_title, test_summary, test_action)

    if result:
        print(json.dumps(result, indent=2))
    else:
        print("Summarization failed -- check the warning above.")