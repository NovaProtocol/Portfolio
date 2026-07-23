from __future__ import annotations

import os
import time
from datetime import datetime

import requests
from cachetools import TTLCache
from flask import jsonify, render_template

from apps.home import blueprint

leetcode_cache = TTLCache(maxsize=1, ttl=300)
LEETCODE_USERNAME = os.environ.get("LEETCODE_USERNAME", "NovaProtocol")


@blueprint.route("/")
def index():
    return render_template("home/index.html")


@blueprint.route("/health")
def health():
    return jsonify({"status": "ok"})


@blueprint.route("/api/leetcode")
def leetcode():
    if "data" in leetcode_cache:
        return jsonify(leetcode_cache["data"])

    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
        "Origin": "https://leetcode.com",
        "Referer": "https://leetcode.com/",
    })

    stats_query = {
        "query": """
        query userStats($username: String!) {
            matchedUser(username: $username) {
                username
                profile { ranking userAvatar realName starRating }
                submitStats { acSubmissionNum { difficulty count } totalSubmissionNum { difficulty count } }
                badges { id name shortName icon hoverText }
                submissionCalendar
            }
        }
        """,
        "variables": {"username": LEETCODE_USERNAME},
    }

    recent_query = {
        "query": """
        query recentAc($username: String!, $limit: Int!) {
            recentAcSubmissionList(username: $username, limit: $limit) { id title titleSlug timestamp }
        }
        """,
        "variables": {"username": LEETCODE_USERNAME, "limit": 20},
    }

    try:
        stats_resp = session.post("https://leetcode.com/graphql", json=stats_query, timeout=10)
        recent_resp = session.post("https://leetcode.com/graphql", json=recent_query, timeout=10)

        user_data = stats_resp.json().get("data", {}).get("matchedUser")
        recent_list = recent_resp.json().get("data", {}).get("recentAcSubmissionList", [])

        submission_calendar = {}
        if user_data and user_data.get("submissionCalendar"):
            submission_calendar = user_data["submissionCalendar"]

        data = {
            "username": user_data.get("username") if user_data else None,
            "profile": user_data.get("profile") if user_data else None,
            "solved": {},
            "totalSubmissions": {},
            "badges": user_data.get("badges", []) if user_data else [],
            "recentSubmissions": [],
            "submissionCalendar": {},
            "fetchedAt": int(time.time()),
        }

        if user_data:
            for entry in user_data.get("submitStats", {}).get("acSubmissionNum", []):
                data["solved"][entry["difficulty"].lower()] = entry["count"]
            for entry in user_data.get("submitStats", {}).get("totalSubmissionNum", []):
                data["totalSubmissions"][entry["difficulty"].lower()] = entry["count"]

        for sub in recent_list:
            data["recentSubmissions"].append({
                "title": sub["title"],
                "slug": sub["titleSlug"],
                "timestamp": int(sub["timestamp"]),
                "date": datetime.utcfromtimestamp(int(sub["timestamp"])).strftime("%Y-%m-%d"),
            })

        if isinstance(submission_calendar, str):
            import json as _json
            data["submissionCalendar"] = _json.loads(submission_calendar)

        leetcode_cache["data"] = data
        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)}), 502
