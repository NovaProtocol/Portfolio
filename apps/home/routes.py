from __future__ import annotations

import json

from flask import jsonify, render_template

from apps.home import blueprint
from apps.leetcode_db import get_all_submissions, get_snapshot


@blueprint.route("/")
def index():
    return render_template("home/index.html")


@blueprint.route("/health")
def health():
    return jsonify({"status": "ok"})


@blueprint.route("/api/leetcode")
def leetcode_api():
    stats_raw = get_snapshot("stats")
    if not stats_raw:
        return jsonify({"error": "No data yet — poller hasn't run"}), 503

    stats = json.loads(stats_raw)
    submissions = get_all_submissions()

    stats["allSubmissions"] = submissions
    return jsonify(stats)


@blueprint.route("/leetcode")
def leetcode_page():
    return render_template("home/leetcode.html")
