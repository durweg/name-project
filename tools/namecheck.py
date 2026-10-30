#!/usr/bin/env python3
"""Check candidate project names for collisions: who already uses each name, and whether they are
active in the same field.

  namecheck.py NAME [NAME ...] [--since YYYY-MM-DD] [--field WORDS] [--inspect] [--json]

For each name: GitHub repositories with the name in their name (how many, how many updated since
--since, and which of those describe themselves with a word from --field), whether a GitHub
account of that name exists, and whether PyPI, npm and crates.io have a package of that name.
--inspect also prints the README start, commit count and last push of each repository flagged as
close, which is what decides whether a name is really taken. Needs `gh` logged in.

A name is "clean" when no repository updated since --since describes itself with a field word.
Stars do not count: a new, active project in the same field takes a name, an old, empty one does not.
"""
import argparse
import base64
import datetime
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

DEFAULT_FIELD = "agent,ai,llm,workflow,claude,codex,gpt,copilot,prompt,multi-agent,mcp,skill"
REGISTRIES = {"pypi": "https://pypi.org/pypi/{}/json", "npm": "https://registry.npmjs.org/{}",
              "crates": "https://crates.io/api/v1/crates/{}"}


def in_field(text, field):
    """Whether a text uses one of the field words, as a whole word ("ai" matches "AI-powered",
    not "said")."""
    text = (text or "").lower()
    return any(re.search(rf"(?<![a-z]){re.escape(w.strip().lower())}(?![a-z])", text) for w in field if w.strip())


def classify(name, repos, since, field):
    """Pure: the summary for one name from the repositories GitHub returned (no network).
    close: updated since `since` and its description is in the field. unclear: updated since
    `since`, exactly this name, but no description to judge by (seen 2026-10-31: an active
    project in the same field had none) - only its README can tell, so look inside (--inspect)."""
    keep = lambda r: {k: r.get(k) for k in ("fullName", "description", "pushedAt", "stargazersCount")}  # noqa: E731
    exact = [r for r in repos if r["fullName"].split("/", 1)[1].lower() == name.lower()]
    recent = [r for r in repos if r.get("pushedAt", "") >= since]
    close = [keep(r) for r in recent if in_field(r.get("description"), field)]
    unclear = [keep(r) for r in recent if r in exact and not (r.get("description") or "").strip()]
    return {"name": name, "repos": len(repos), "exact": len(exact), "recent": len(recent),
            "close": close, "unclear": unclear, "clean": not close and not unclear}


def gh_json(args):
    r = subprocess.run(["gh", *args], capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout or "null")
    except ValueError:
        return None


def http_status(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "naming-workflow namecheck"})
        return urllib.request.urlopen(req, timeout=10).status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return None


def inspect(full_name):
    info = gh_json(["api", f"repos/{full_name}"]) or {}
    commits = gh_json(["api", f"repos/{full_name}/commits?per_page=100"]) or []
    readme = gh_json(["api", f"repos/{full_name}/readme"]) or {}
    try:
        text = base64.b64decode(readme.get("content", "")).decode("utf-8", "replace")
    except ValueError:
        text = ""
    head = " ".join(" ".join(text.split()).split(" ")[:40])
    return {"commits": f"{len(commits)}{'+' if len(commits) == 100 else ''}", "language": info.get("language"),
            "created": (info.get("created_at") or "")[:10], "readme": head}


def check(name, since, field, do_inspect):
    repos = gh_json(["search", "repos", f"{name} in:name", "--limit", "30", "--json",
                     "fullName,description,pushedAt,stargazersCount"]) or []
    result = classify(name, repos, since, field)
    user = gh_json(["api", f"users/{name}"])
    result["account"] = f"{user.get('type')} with {user.get('public_repos')} repositories" if user else "free"
    for key, url in REGISTRIES.items():
        status = http_status(url.format(name))
        result[key] = "free" if status == 404 else "taken" if status == 200 else f"unknown ({status})"
    if do_inspect:
        for r in result["close"] + result["unclear"]:
            r.update(inspect(r["fullName"]))
        # An unclear repository whose README is in the field is close; one whose README is not, is not.
        result["close"] += [r for r in result["unclear"] if in_field(r["readme"], field)]
        result["unclear"] = []
        result["clean"] = not result["close"]
    return result


def main(argv):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("names", nargs="+")
    p.add_argument("--since", default=(datetime.date.today() - datetime.timedelta(days=365)).isoformat())
    p.add_argument("--field", default=DEFAULT_FIELD, help="comma-separated words of the project's field")
    p.add_argument("--inspect", action="store_true")
    p.add_argument("--json", action="store_true")
    a = p.parse_args(argv)
    results = []
    for i, name in enumerate(a.names):
        if i:
            time.sleep(2.5)                 # GitHub's search allows about 30 requests a minute
        results.append(check(name, a.since, a.field.split(","), a.inspect))
    if a.json:
        print(json.dumps(results, indent=1, ensure_ascii=False))
        return 0
    for r in results:
        verdict = "TAKEN" if r["close"] else "CHECK" if r["unclear"] else "CLEAN"
        print(f"{r['name']:14} {verdict}  repos {r['repos']} (same name {r['exact']}, "
              f"updated since {a.since}: {r['recent']})  account {r['account']}  "
              f"pypi {r['pypi']}  npm {r['npm']}  crates {r['crates']}")
        for c in r["unclear"]:
            print(f"    ? {c['fullName']} {c['stargazersCount']}* pushed {c['pushedAt'][:10]}: no description; run with --inspect")
        for c in r["close"]:
            print(f"    ! {c['fullName']} {c['stargazersCount']}* pushed {c['pushedAt'][:10]}: {(c['description'] or '')[:90]}")
            if "readme" in c:
                print(f"      {c['commits']} commits, {c['language']}, created {c['created']}: {c['readme'][:160]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
