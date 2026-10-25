"""
tests_app.py
Unit tests for the API server. Run with:  python -m unittest tests_app
(No API keys or network needed.)
"""

import json
import unittest

from app import app, is_placeholder
from generate_cache import is_placeholder as is_placeholder_raw


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json(), {"status": "ok"})

    def test_bills_shape(self):
        res = self.client.get("/bills")
        self.assertEqual(res.status_code, 200)
        bills = res.get_json()
        self.assertIsInstance(bills, list)
        self.assertGreater(len(bills), 0)
        required = {"id", "plain_title", "plain_summary", "key_provisions", "topics", "status_plain_english"}
        for bill in bills:
            self.assertTrue(required <= bill.keys(), bill.get("id"))

    def test_bills_allow_cross_origin(self):
        res = self.client.get("/bills", headers={"Origin": "https://example.com"})
        self.assertIn("Access-Control-Allow-Origin", res.headers)

    def test_placeholder_detection(self):
        self.assertTrue(is_placeholder({"original_title": "Reserved for the Speaker."}))
        self.assertFalse(is_placeholder({"original_title": "Taiwan Flag Act"}))
        self.assertTrue(is_placeholder_raw({"title": "Reserved for the Minority Leader."}))


class CacheFileTests(unittest.TestCase):
    def test_cache_is_valid(self):
        with open("bills_cache.json", encoding="utf-8") as f:
            bills = json.load(f)
        ids = [b["id"] for b in bills]
        self.assertEqual(len(ids), len(set(ids)), "duplicate bill ids")
        for b in bills:
            self.assertIn(b.get("source"), {"official_summary", "bill_text", "title_only"})


if __name__ == "__main__":
    unittest.main()
