#!/usr/bin/env python3
"""Update the README "Recent Activity" block from public GitHub events.

Runs in GitHub Actions (see .github/workflows/activity.yml). Safe by design:
if the API call fails, it leaves the README untouched and exits 0 so the
workflow never fails noisily.
"""
import datetime
import json
import os
import re
import urllib.request

USER = "abhijeetgupta02"
README = "README.md"
START = "<!--START_SECTION:activity-->"
END = "<!--END_SECTION:activity-->"


def fetch_events():
    req = urllib.request.Request(
        f"https://api.github.com/users/{USER}/events/public?per_page=40",
        headers={
            "Authorization": f"Bearer {os.environ.get('GH_TOKEN', '')}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "profile-activity-bot",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def describe(event):
    t = event.get("type")
    repo = event.get("repo", {}).get("name", "")
    url = f"https://github.com/{repo}"
    if t == "PushEvent":
        commits = event.get("payload", {}).get("commits", [])
        if commits:
            msg = commits[-1]["message"].splitlines()[0][:72]
            return f"📌 Pushed to [`{repo}`]({url}): {msg}"
    elif t == "ReleaseEvent":
        tag = event["payload"]["release"]["tag_name"]
        return f"🚀 Released `{tag}` in [`{repo}`]({url})"
    elif t == "CreateEvent":
        ref = event["payload"].get("ref_type", "")
        return f"✨ Created {ref} in [`{repo}`]({url})"
    elif t == "PullRequestEvent" and event["payload"].get("action") == "opened":
        return f"🔀 Opened a PR in [`{repo}`]({url})"
    elif t == "WatchEvent":
        return f"⭐ Starred [`{repo}`]({url})"
    return None


def main():
    try:
        events = fetch_events()
    except Exception as exc:  # noqa: BLE001 - never fail the workflow over this
        print(f"Could not fetch events ({exc}); leaving README unchanged.")
        return

    lines, seen = [], set()
    for event in events:
        item = describe(event)
        if item and item not in seen:
            seen.add(item)
            lines.append("- " + item)
        if len(lines) >= 5:
            break
    if not lines:
        lines = ["- _Recent public activity will appear here._"]

    body = "\n".join(lines) + f"\n\n_Last updated: {datetime.date.today().isoformat()}_"
    block = f"{START}\n{body}\n{END}"

    with open(README, encoding="utf-8") as fh:
        readme = fh.read()
    new = re.sub(re.escape(START) + ".*?" + re.escape(END), block, readme, flags=re.S)
    if new != readme:
        with open(README, "w", encoding="utf-8") as fh:
            fh.write(new)
        print("Recent Activity updated.")
    else:
        print("No change.")


if __name__ == "__main__":
    main()
