"""
app.py
The Flask API server. Serves pre-generated bill summaries from a cache
file instantly -- no live API calls during page load.
"""

import json
import os
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

CACHE_FILE = "bills_cache.json"


@app.route("/bills", methods=["GET"])
def get_bills():
    """Return cached, pre-summarized bills -- instant, no Claude calls here."""
    if not os.path.exists(CACHE_FILE):
        return jsonify({
            "error": "No cached data yet. Run 'python generate_cache.py' first."
        }), 404

    with open(CACHE_FILE, "r") as f:
        bills = json.load(f)

    return jsonify(bills)


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)