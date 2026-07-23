from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from threading import Thread

import requests

from apps.leetcode_db import (
    get_all_submissions,
    get_snapshot,
    init_db,
    save_snapshot,
    upsert_submissions,
)

logger = logging.getLogger(__name__)
LEETCODE_USERNAME = os.environ.get("LEETCODE_USERNAME", "NovaProtocol")
POLL_INTERVAL = 600  # 10 minutes


def fetch_leetcode_data() -> dict | None:
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
        "Origin": "https://leetcode.com",
        "Referer": "https://leetcode.com/",
    })

    query = """
    query userStats($username: String!) {
        matchedUser(username: $username) {
            username
            profile { ranking userAvatar realName starRating }
            submitStats { acSubmissionNum { difficulty count } totalSubmissionNum { difficulty count } }
            badges { id name shortName icon hoverText }
            submissionCalendar
        }
    }
    """

    recent_query = """
    query recentAc($username: String!, $limit: Int!) {
        recentAcSubmissionList(username: $username, limit: $limit) { id title titleSlug timestamp }
    }
    """

    try:
        stats_resp = session.post(
            "https://leetcode.com/graphql",
            json={"query": query, "variables": {"username": LEETCODE_USERNAME}},
            timeout=15,
        )
        recent_resp = session.post(
            "https://leetcode.com/graphql",
            json={"query": recent_query, "variables": {"username": LEETCODE_USERNAME, "limit": 20}},
            timeout=15,
        )

        user_data = stats_resp.json().get("data", {}).get("matchedUser")
        recent_list = recent_resp.json().get("data", {}).get("recentAcSubmissionList", [])

        if not user_data:
            return None

        solved = {}
        for entry in user_data.get("submitStats", {}).get("acSubmissionNum", []):
            solved[entry["difficulty"].lower()] = entry["count"]

        total_sub = {}
        for entry in user_data.get("submitStats", {}).get("totalSubmissionNum", []):
            total_sub[entry["difficulty"].lower()] = entry["count"]

        submission_calendar = user_data.get("submissionCalendar", "{}")
        if isinstance(submission_calendar, str):
            submission_calendar = json.loads(submission_calendar)

        recent = []
        for sub in recent_list:
            ts = int(sub["timestamp"])
            recent.append({
                "id": sub["id"],
                "title": sub["title"],
                "slug": sub["titleSlug"],
                "timestamp": ts,
                "date": datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d"),
            })

        return {
            "username": user_data.get("username"),
            "profile": user_data.get("profile"),
            "solved": solved,
            "totalSubmissions": total_sub,
            "badges": user_data.get("badges", []),
            "recentSubmissions": recent,
            "submissionCalendar": submission_calendar,
            "fetchedAt": int(time.time()),
        }

    except Exception as e:
        logger.warning("LeetCode poll failed: %s", e)
        return None


def poll_loop() -> None:
    init_db()
    logger.info("LeetCode poller started (interval=%ss)", POLL_INTERVAL)

    while True:
        data = fetch_leetcode_data()
        if data:
            save_snapshot("stats", json.dumps({
                "username": data["username"],
                "profile": data["profile"],
                "solved": data["solved"],
                "totalSubmissions": data["totalSubmissions"],
                "badges": data["badges"],
                "submissionCalendar": data["submissionCalendar"],
                "fetchedAt": data["fetchedAt"],
            }))
            new = upsert_submissions(data["recentSubmissions"])
            if new > 0:
                logger.info("LeetCode: %d new submission(s) stored", new)
            logger.debug("LeetCode poll complete: %d solved", data["solved"].get("all", 0))
        else:
            logger.warning("LeetCode poll returned no data")

        time.sleep(POLL_INTERVAL)


def start_poller() -> None:
    thread = Thread(target=poll_loop, daemon=True, name="leetcode-poller")
    thread.start()
