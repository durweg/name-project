#!/usr/bin/env python3
"""wf gate for step 4 of name-project (design WP-R-004/005/012): every candidate was really checked.

  verify_check.py RUN

Reads steps/3-candidates.json, steps/4-check.json and every checks/*.record.json (written by
`namecheck.py --record`). For each candidate it computes, from the records only, one state:

  checked     a record has its result (exact name, case-insensitive), without error, not
              incomplete, with an answer from GitHub's account check and every registry; and if the
              name is not clean, an --inspect record read every flagged repository (read: true)
  unresolved  error | incomplete | registry-unknown | inspect-failed

A name that is not clean in its latest record, when that record was not an --inspect run, stops
the gate: the inspect step is missing (it is not an allowed unresolved state).

The state written in 4-check.json must equal the computed one. The proposed set may hold only
checked names, each with three searches recorded (web_plain, web_field, trademark). Every record
must use the --field and --since given in 4-check.json and the namecheck of this run's snapshot.
namecheck's exit code is not used: it exits 0 even when a name could not be checked.

Exit 1 with one line per problem. Standard library only (wf snapshot rule).
"""
import datetime
import hashlib
import json
import os
import sys
from pathlib import Path

SEARCHES = ("web_plain", "web_field", "trademark")
SEARCH_FIELDS = ("query", "date", "sources", "conclusion")


def load(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        sys.exit(f"cannot read {p}: {e}")


def key(name):
    return " ".join(str(name).split()).lower()


REASONS = ("error", "incomplete", "registry-unknown", "inspect-failed")


def compute_state(name, records):
    """(state, reason) for one name from the records that contain it (records sorted oldest first).

    The latest record that has the name decides (WP-P-003). If that result is not clean, it must
    itself come from an --inspect run, so that every repository it flags was looked at: an older
    inspect does not cover repositories found later. Returns ("not-inspected", repos) when no such
    inspect exists - that is a missing step, not an allowed state.
    """
    found = [(rec, r) for rec in records for r in rec.get("results", []) if key(r.get("name")) == key(name)]
    if not found:
        return "missing", "no namecheck record has this name"
    rec, r = found[-1]
    if "error" in r:
        return "unresolved", "error"
    if r.get("incomplete"):
        return "unresolved", "incomplete"
    answers = [r.get("account", "")] + [r.get(k, "") for k in ("pypi", "npm", "crates")]
    if any(not isinstance(a, str) or not a or a.startswith("unknown") for a in answers):
        return "unresolved", "registry-unknown"
    flagged = (r.get("close") or []) + (r.get("unclear") or [])
    if not flagged:
        return "checked", None
    if not rec.get("inspect"):
        repos = ", ".join(sorted(str(x.get("fullName")) for x in flagged))
        return "not-inspected", f"the latest check ({rec['_file']}) flags {repos} and was not an --inspect run"
    if r.get("unclear") or any(x.get("read") is not True for x in flagged):
        return "unresolved", "inspect-failed"
    return "checked", None


def is_date(s):
    try:
        datetime.date.fromisoformat(str(s)[:10])
        return isinstance(s, str) and len(s) >= 10
    except ValueError:
        return False


def text(v):
    return isinstance(v, str) and v.strip() and v.strip().lower() not in ("todo", "tbd", "-", "?", "…", "...")


def record_problems(rec):
    """Minimal structure of a namecheck --record file (WP-P-002)."""
    f, errs = rec["_file"], []
    if rec.get("tool") != "namecheck":
        errs.append(f"{f}: not a namecheck record")
    if not isinstance(rec.get("sha256"), str) or len(rec["sha256"]) != 64:
        errs.append(f"{f}: no sha256 of namecheck.py")
    try:
        datetime.datetime.fromisoformat(rec.get("started_at", ""))
    except (TypeError, ValueError):
        errs.append(f"{f}: started_at is not a time")
    if not isinstance(rec.get("inspect"), bool):
        errs.append(f"{f}: inspect must be true or false")
    names, results = rec.get("names"), rec.get("results")
    if not isinstance(names, list) or not all(isinstance(n, str) for n in names):
        errs.append(f"{f}: names must be a list of names")
    elif not isinstance(results, list) or not all(isinstance(r, dict) for r in results):
        errs.append(f"{f}: results must be a list of objects")
    elif [key(r.get("name")) for r in results] != [key(n) for n in names]:
        errs.append(f"{f}: results do not match the names checked")
    return errs


def main(argv):
    if len(argv) != 1:
        sys.exit(__doc__)
    run = Path(argv[0])
    errs = []
    cands = [c.get("name") for c in load(run / "steps/3-candidates.json").get("candidates", [])]
    chk = load(run / "steps/4-check.json")
    paths = sorted((run / "checks").glob("*.record.json"))
    records = [load(p) for p in paths]
    for p, rec in zip(paths, records):
        rec["_file"] = p.name
    records.sort(key=lambda r: (r.get("started_at", ""), r["_file"]))
    if not records:
        errs.append("no checks/*.record.json: run namecheck.py with --record")

    # how the checks were made
    field = sorted(key(w) for w in chk.get("field", []))
    snap = os.environ.get("WF_SNAPSHOT")
    want_sha = None
    if snap and (Path(snap) / "tools/namecheck.py").is_file():
        want_sha = hashlib.sha256((Path(snap) / "tools/namecheck.py").read_bytes()).hexdigest()
    for rec in records:
        errs += record_problems(rec)
        if sorted(key(w) for w in rec.get("field", [])) != field:
            errs.append(f"{rec['_file']}: --field {rec.get('field')} differs from 4-check.json {chk.get('field')}")
        if rec.get("since") != chk.get("since"):
            errs.append(f"{rec['_file']}: --since {rec.get('since')} differs from 4-check.json {chk.get('since')}")
        if want_sha and rec.get("sha256") != want_sha:
            errs.append(f"{rec['_file']}: made by another namecheck.py than this run's (sha256)")

    # every candidate: computed state = declared state
    declared = {key(k): v for k, v in (chk.get("candidates") or {}).items()}
    checked = set()
    for name in cands:
        state, reason = compute_state(name, records)
        d = declared.get(key(name))
        if state in ("missing", "not-inspected"):
            errs.append(f"{name}: {reason}")
            continue
        if not isinstance(d, dict) or d.get("state") not in ("checked", "unresolved") or \
                (d.get("state") == "unresolved" and d.get("reason") not in REASONS):
            errs.append(f"{name}: 4-check.json must say {{\"state\": \"checked\"}} or "
                        f"{{\"state\": \"unresolved\", \"reason\": one of {list(REASONS)}}}")
            continue
        if d.get("state") != state or (state == "unresolved" and d.get("reason") != reason):
            errs.append(f"{name}: 4-check.json says {d.get('state')}/{d.get('reason')}, the records say "
                        f"{state}/{reason}")
        if state == "checked":
            checked.add(key(name))
    extra = set(declared) - {key(n) for n in cands}
    for x in sorted(extra):
        errs.append(f"{x}: in 4-check.json but not a candidate of step 3")

    # proposed set
    seen = set()
    for p in chk.get("proposed", []):
        if not isinstance(p, dict):
            errs.append("proposed items must be objects")
            continue
        n = p.get("name", "")
        if key(n) in seen:
            errs.append(f"{n}: proposed more than once")
        seen.add(key(n))
        if key(n) not in checked:
            errs.append(f"{n}: proposed but not checked (unresolved or unknown names cannot be proposed)")
        for s in SEARCHES:
            q = p.get(s)
            if not isinstance(q, dict):
                errs.append(f"{n}: {s} search must be an object with {', '.join(SEARCH_FIELDS)}")
                continue
            bad = [f for f in ("query", "conclusion") if not text(q.get(f))]
            if not is_date(q.get("date")):
                bad.append("date (YYYY-MM-DD)")
            src = q.get("sources")
            if not isinstance(src, list) or not src or not all(text(x) for x in src):
                bad.append("sources (a list of non-empty texts)")
            if bad:
                errs.append(f"{n}: {s} search lacks {', '.join(bad)}")
    if not chk.get("proposed"):
        errs.append("the proposed set is empty: nothing can go on the short list")
    for e in errs:
        print(e)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
