"""
summarize_bill.py
Takes raw bill data from Congress.gov and uses Claude to produce a
structured, plain-English JSON summary for high school readers.
"""

import json

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment

MODEL = "claude-opus-5-5"

TOPICS = [
    "Education", "Immigration", "Healthcare", "Climate", "Economy",
    "Civil Rights", "Criminal Justice", "Technology", "Foreign Policy", "Other",
]

# Structured outputs guarantee the reply matches this schema exactly.
SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "plain_title": {"type": "string"},
        "plain_summary": {"type": "string"},
        "key_provisions": {"type": "array", "items": {"type": "string"}},
        "who_it_affects": {"type": "string"},
        "why_it_matters": {"type": "string"},
        "topics": {"type": "array", "items": {"type": "string", "enum": TOPICS}},
        "status_plain_english": {"type": "string"},
    },
    "required": [
        "plain_title", "plain_summary", "key_provisions", "who_it_affects",
        "why_it_matters", "topics", "status_plain_english",
    ],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """You translate U.S. congressional bills into plain English for high school students who have little background in civics or legal language.

Accuracy matters more than detail. Describe only what the official information says: the official summary and the bill text are the sources of truth. If neither is available, work from the title and latest action alone: say what the bill appears to do based on its title, keep it short, and do not invent specific numbers, programs, dates or requirements.

Field guide:
- plain_title: a short, clear title a teenager would understand (12 words max).
- plain_summary: 2-3 sentences on what the bill does, for someone with zero background. No legal jargon. Use a concrete example when the official text supports one.
- key_provisions: 2-4 short phrases, one per main provision, taken from the bill text when it is provided. If only the title is available, give 1-2.
- who_it_affects: one sentence on which groups of people this would affect and how.
- why_it_matters: one sentence connecting the bill to the life of a high schooler or young future voter (school, jobs, money, safety, health, family, the future). Be honest; if the link is indirect, say so plainly.
- topics: 1-3 topics from the allowed list.
- status_plain_english: one sentence translating the latest action into plain English (for example, "This bill was just introduced and sent to a committee, so it hasn't been voted on yet").

Write in plain, neutral language. Do not take a side on whether the bill is good or bad."""

USER_TEMPLATE = """Official title: {title}
Official summary: {official_summary}
Latest action: {latest_action}

<bill_text>
{bill_text}
</bill_text>"""


def summarize_bill(title, official_summary, latest_action, bill_text=""):
    """Return a dict summary for one bill, or None if Claude declined or failed."""
    try:
        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=4000,
            # Simple extraction task: low effort keeps it fast and cheap
            output_config={
                "effort": "low",
                "format": {"type": "json_schema", "schema": SUMMARY_SCHEMA},
            },
            # If a safety classifier declines, retry on Anthropic's recommended fallback model
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": USER_TEMPLATE.format(
                    title=title,
                    official_summary=official_summary or "None published yet.",
                    latest_action=latest_action or "No action recorded yet.",
                    bill_text=bill_text or "Not published yet.",
                ),
            }],
        )
    except anthropic.RateLimitError:
        print("   Rate limited by the Claude API (the SDK already retried).")
        return None
    except anthropic.APIStatusError as e:
        print(f"   Claude API error {e.status_code}: {e.message}")
        return None
    except anthropic.APIConnectionError:
        print("   Could not reach the Claude API.")
        return None

    if response.stop_reason == "refusal":
        print("   Claude declined to summarize this bill.")
        return None
    if response.stop_reason == "max_tokens":
        print("   Summary was cut off (max_tokens).")
        return None

    text = next((b.text for b in response.content if b.type == "text"), "")
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"   Could not parse Claude's response as JSON: {e}")
        return None


if __name__ == "__main__":
    test_title = "A bill to require schools to teach personal financial literacy"
    test_summary = (
        "This bill requires public secondary schools to include a personal financial "
        "literacy course as part of the standard curriculum, covering budgeting, credit, "
        "taxes, and saving for retirement."
    )
    test_action = "Referred to the Committee on Education and the Workforce."

    print("Testing summarization pipeline...\n")
    result = summarize_bill(test_title, test_summary, test_action)
    print(json.dumps(result, indent=2) if result else "Summarization failed -- see above.")
