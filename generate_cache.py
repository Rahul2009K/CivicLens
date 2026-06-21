"""
generate_cache.py
Pre-generates bill summaries and saves them to a local JSON file.
Run this script manually whenever you want to refresh the bill data.
This keeps the slow Claude API calls separate from serving the website,
so the website itself loads instantly.
"""

import json
from fetch_bills import fetch_recent_bills, get_summary_text
from summarize_bill import summarize_bill

CACHE_FILE = "bills_cache.json"
NUMBER_OF_BILLS = 10


def generate_cache():
    print(f"Fetching {NUMBER_OF_BILLS} recent bills...")
    data = fetch_recent_bills(limit=NUMBER_OF_BILLS)
    bills = data.get("bills", [])

    results = []
    for i, bill in enumerate(bills, start=1):
        print(f"Processing bill {i}/{len(bills)}: {bill.get('title', '')[:50]}")
        official_summary = get_summary_text(bill)
        latest_action = bill.get("latestAction", {}).get("text", "")
        summary = summarize_bill(bill.get("title", ""), official_summary, latest_action)

        if summary:
            results.append({
                "id": f"{bill.get('congress')}-{bill.get('type')}-{bill.get('number')}",
                "original_title": bill.get("title"),
                **summary,
            })
            print(f"  Done with bill {i}")
        else:
            print(f"  Bill {i} failed to summarize -- skipping")

    with open(CACHE_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved {len(results)} summarized bills to {CACHE_FILE}")


if __name__ == "__main__":
    generate_cache()