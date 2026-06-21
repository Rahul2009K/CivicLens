"""
test_pipeline.py
Pulls real bills and runs them through the summarization pipeline,
saving results to a JSON file so you can review them for accuracy.
"""
from fetch_bills import fetch_recent_bills, get_summary_text
import json
import time
from fetch_bills import fetch_recent_bills
from summarize_bill import summarize_bill

NUMBER_OF_BILLS_TO_TEST = 10
OUTPUT_FILE = "test_results.json"


def run_test_batch():
    print(f"Fetching {NUMBER_OF_BILLS_TO_TEST} bills from Congress.gov...")
    data = fetch_recent_bills(limit=NUMBER_OF_BILLS_TO_TEST)
    bills = data.get("bills", [])

    results = []

    for i, bill in enumerate(bills, start=1):
        title = bill.get("title", "Untitled bill")
        latest_action = bill.get("latestAction", {}).get("text", "")
        official_summary = get_summary_text(bill)

        print(f"[{i}/{len(bills)}] Summarizing: {title[:60]}...")

        summary = summarize_bill(title, official_summary, latest_action)

        results.append({
            "original_title": title,
            "original_latest_action": latest_action,
            "claude_summary": summary,
        })

        time.sleep(1)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nDone. Saved {len(results)} results to {OUTPUT_FILE}")
    print("Now: open that file and manually review at least 6 of the 30 (20%) for accuracy.")


if __name__ == "__main__":
    run_test_batch()