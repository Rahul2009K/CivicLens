"""
generate_cache.py
Pre-generates bill summaries and saves them to bills_cache.json.
Run this manually whenever you want to refresh the bill data. Keeping the
slow Claude calls here means the website itself loads instantly.

It also writes a copy into the frontend (public/bills.json) when that repo
sits next to this one, so the site can show bills even while the API sleeps.
"""

import json
import os
import shutil
from concurrent.futures import ThreadPoolExecutor

from fetch_bills import fetch_recent_bills, fetch_bill_detail, get_bill_text, get_summary_text
from summarize_bill import summarize_bill

CACHE_FILE = "bills_cache.json"
FRONTEND_SNAPSHOT = os.path.join("..", "civiclens-frontend", "public", "bills.json")
NUMBER_OF_BILLS = 100
FETCH_EXTRA = 40      # placeholders and failures get skipped, so fetch a few more
WORKERS = 6           # parallel bills; the SDK retries if we hit rate limits


def is_placeholder(bill):
    """Bill numbers reserved for House leadership have no real content."""
    return (bill.get("title") or "").strip().lower().startswith("reserved for")


def bill_facts(bill):
    """Sponsor, dates and cosponsor count from the bill's detail record."""
    try:
        detail = fetch_bill_detail(bill["congress"], bill["type"].lower(), bill["number"]).get("bill", {})
    except Exception as e:
        print(f"   Could not fetch details for {bill.get('number')}: {e}")
        return {}
    sponsor = (detail.get("sponsors") or [{}])[0]
    return {
        "sponsor": {
            "name": sponsor.get("fullName"),
            "party": sponsor.get("party"),
            "state": sponsor.get("state"),
        } if sponsor else None,
        "introduced_date": detail.get("introducedDate"),
        "cosponsor_count": (detail.get("cosponsors") or {}).get("count", 0),
        "policy_area": (detail.get("policyArea") or {}).get("name"),
    }


def process(bill):
    official_summary = get_summary_text(bill)
    latest = bill.get("latestAction") or {}
    bill_text = get_bill_text(bill)
    summary = summarize_bill(bill.get("title", ""), official_summary, latest.get("text", ""), bill_text)
    if not summary:
        return None
    return {
        "id": f"{bill.get('congress')}-{bill.get('type')}-{bill.get('number')}",
        "original_title": bill.get("title"),
        **summary,
        # What the plain-English version was written from, most to least authoritative
        "source": "official_summary" if official_summary else "bill_text" if bill_text else "title_only",
        "title_only": not official_summary and not bill_text,
        "latest_action_date": latest.get("actionDate"),
        "latest_action_text": latest.get("text"),
        "update_date": bill.get("updateDate"),
        **bill_facts(bill),
    }


def generate_cache():
    print(f"Fetching {NUMBER_OF_BILLS + FETCH_EXTRA} recent bills...")
    bills = fetch_recent_bills(limit=NUMBER_OF_BILLS + FETCH_EXTRA).get("bills", [])
    skipped = [b for b in bills if is_placeholder(b)]
    bills = [b for b in bills if not is_placeholder(b)]
    print(f"Skipping {len(skipped)} placeholder bills. Summarizing {len(bills)} candidates...")

    results = []
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for i, item in enumerate(pool.map(process, bills), start=1):
            if item:
                results.append(item)
                print(f"  [{i}/{len(bills)}] {item['id']}: {item['plain_title'][:60]}")
            else:
                print(f"  [{i}/{len(bills)}] failed -- skipping")

    # pool.map keeps the API's newest-first order; keep the newest N
    results = results[:NUMBER_OF_BILLS]

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(results)} summarized bills to {CACHE_FILE}")

    if os.path.isdir(os.path.dirname(FRONTEND_SNAPSHOT)):
        shutil.copyfile(CACHE_FILE, FRONTEND_SNAPSHOT)
        print(f"Copied snapshot to {FRONTEND_SNAPSHOT}")


if __name__ == "__main__":
    generate_cache()
