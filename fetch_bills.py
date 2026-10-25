"""
fetch_bills.py
Pulls the most recent bills from Congress.gov and prints their raw data.
"""

import html
import os
import re

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("CONGRESS_API_KEY")
BASE_URL = "https://api.congress.gov/v3"


def fetch_recent_bills(limit=20):
    """Fetch recent bills specifically from the 119th Congress (2025-2026)."""
    url = f"{BASE_URL}/bill/119"
    params = {
        "api_key": API_KEY,
        "limit": limit,
        "sort": "updateDate+desc",
        "format": "json",
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def fetch_bill_detail(congress, bill_type, bill_number):
    """Fetch full detail for a single bill, including its summary text."""
    url = f"{BASE_URL}/bill/{congress}/{bill_type}/{bill_number}"
    params = {"api_key": API_KEY, "format": "json"}
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def fetch_bill_summary_text(congress, bill_type, bill_number):
    """Fetch the official summary text for a bill."""
    url = f"{BASE_URL}/bill/{congress}/{bill_type}/{bill_number}/summaries"
    params = {"api_key": API_KEY, "format": "json"}
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def get_summary_text(bill):
    """Pull the real official summary for a single bill, with a fallback
    if no summary exists yet."""
    congress = bill.get("congress")
    bill_type = bill.get("type", "").lower()
    bill_number = bill.get("number")

    try:
        summary_data = fetch_bill_summary_text(congress, bill_type, bill_number)
        summaries = summary_data.get("summaries", [])
        if summaries:
            return summaries[0].get("text", "")
    except Exception as e:
        print(f"   Could not fetch summary for bill {bill_number}: {e}")

    return ""


if __name__ == "__main__":
    if not API_KEY:
        print("ERROR: CONGRESS_API_KEY not found. Did you create your .env file?")
        exit(1)

    print("Fetching 20 recent bills...\n")
    data = fetch_recent_bills(limit=20)

    bills = data.get("bills", [])
    print(f"Got {len(bills)} bills back.\n")

    for i, bill in enumerate(bills, start=1):
        print(f"{i}. {bill.get('title', 'NO TITLE')}")
        print(f"   Congress: {bill.get('congress')}, Type: {bill.get('type')}, Number: {bill.get('number')}")
        print(f"   Latest action: {bill.get('latestAction', {}).get('text', 'N/A')}")
        print(f"   Summary: {get_summary_text(bill)}")

MAX_TEXT_CHARS = 40000  # roughly 10k tokens; very long bills are trimmed with a note


def get_bill_text(bill):
    """Plain text of the latest published version of a bill, or "" if none."""
    congress = bill.get("congress")
    bill_type = bill.get("type", "").lower()
    number = bill.get("number")
    try:
        url = f"{BASE_URL}/bill/{congress}/{bill_type}/{number}/text"
        versions = requests.get(url, params={"api_key": API_KEY, "format": "json"}, timeout=30).json().get("textVersions", [])
        formats = [f for v in versions for f in v.get("formats", []) if f.get("type") == "Formatted Text"]
        if not formats:
            return ""
        raw = requests.get(formats[0]["url"], timeout=30).text
    except Exception as e:
        print(f"   Could not fetch text for bill {number}: {e}")
        return ""
    text = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
    if len(text) > MAX_TEXT_CHARS:
        text = text[:MAX_TEXT_CHARS] + "\n\n[Bill text trimmed for length.]"
    return text
