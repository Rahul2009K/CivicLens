"""
fetch_bills.py
Pulls the most recent bills from Congress.gov and prints their raw data.
This is purely for exploration -- we're learning the shape of the data
before we try to transform it.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("CONGRESS_API_KEY")
BASE_URL = "https://api.congress.gov/v3"


def fetch_recent_bills(limit=20):
    """Fetch the most recent bills introduced in Congress."""
    url = f"{BASE_URL}/bill"
    params = {
        "api_key": API_KEY,
        "limit": limit,
        "sort": "updateDate+desc",  # most recently updated first
        "format": "json",
    }
    response = requests.get(url, params=params)
    response.raise_for_status()  # crashes loudly if something's wrong -- good, we want to know
    return response.json()


def fetch_bill_detail(congress, bill_type, bill_number):
    """Fetch full detail for a single bill, including its summary text."""
    url = f"{BASE_URL}/bill/{congress}/{bill_type}/{bill_number}"
    params = {"api_key": API_KEY, "format": "json"}
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def fetch_bill_summary_text(congress, bill_type, bill_number):
    """Fetch the official summary text for a bill -- this is what we'll
    feed to Claude for plain-English translation."""
    url = f"{BASE_URL}/bill/{congress}/{bill_type}/{bill_number}/summaries"
    params = {"api_key": API_KEY, "format": "json"}
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def get_summary_text(bill):
    """Pull the real official summary for a single bill, with a fallback
    if no summary exists yet (some newly introduced bills don't have one)."""
    congress = bill.get("congress")
    bill_type = bill.get("type", "").lower()
    bill_number = bill.get("number")

    try:
        summary_data = fetch_bill_summary_text(congress, bill_type, bill_number)
        summaries = summary_data.get("summaries", [])
        if summaries:
            # Summaries are returned newest first -- take the most recent one
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
        print()