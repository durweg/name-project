#!/usr/bin/env python3
"""wf gate for step 4 of name-project (design WP-R-004/005/012): every candidate was really checked.

  verify_check.py RUN

Reads steps/3-candidates.json, steps/4-check.json and every checks/*.record.json (written by
`namecheck.py --record`). For each candidate it computes, from the records only, one state:

  checked     a record has its result (exact name, case-insensitive), without error, not
              incomplete, with an answer from GitHub's account check and every registry; and if the
              name is not clean, an --inspect record read every flagged repository (read: true)
  unresolved  error | incomplete | registry-unknown | inspect-failed | not-inspected

The state written in 4-check.json must equal the computed one. The proposed set may hold only
checked names, each with three searches recorded (web_plain, web_field, trademark). Every record
must use the --field and --since given in 4-check.json and the namecheck of this run's snapshot.
namecheck's exit code is not used: it exits 0 even when a name could not be checked.

Exit 1 with one line per problem. Standard library only (wf snapshot rule).
"""
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


def compute_state(name, records):
    """(state, reason) for one name from the records that contain it, latest last."""
    found = [(rec, r) for rec in records for r in rec.get("results", []) if key(r.get("name")) == key(name)]
    if not found:
        return "missing", "no namecheck record has this name"
    rec, r = found[-1]
    if "error" in r:
        return "unresolved", "error"
    if r.get("incomplete"):
        return "unresolved", "incomplete"
    answers = [r.get("account", "")] + [r.get(k, "") for k in ("pypi", "npm", "crates")]
    if any(not a or str(a).startswith("unknown") for a in answers):
        return "unresolved", "registry-unknown"
    flagged = (r.get("close") or []) + (r.get("unclear") or [])
    if not flagged:
        return "checked", None
    inspected = [(rc, x) for rc, x in found if rc.get("inspect")]
    if not inspected:
        return "unresolved", "not-inspected"
    rec, r = inspected[-1]
    flagged = (r.get("close") or []) + (r.get("unclear") or [])
    if r.get("unclear") or any(x.get("read") is not True for x in flagged):
        return "unresolved", "inspect-failed"
    return "checked", None


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
        if rec.get("tool") != "namecheck":
            errs.append(f"{rec['_file']}: not a namecheck record")
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
        if state == "missing":
            errs.append(f"{name}: {reason}")
            continue
        if not d:
            errs.append(f"{name}: missing from 4-check.json candidates (computed: {state}"
                        f"{' ' + reason if reason else ''})")
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
    for p in chk.get("proposed", []):
        n = p.get("name", "")
        if key(n) not in checked:
            errs.append(f"{n}: proposed but not checked (unresolved or unknown names cannot be proposed)")
        for s in SEARCHES:
            q = p.get(s) or {}
            missing = [f for f in SEARCH_FIELDS if not q.get(f)]
            if missing:
                errs.append(f"{n}: {s} search lacks {', '.join(missing)}")
    if not chk.get("proposed"):
        errs.append("the proposed set is empty: nothing can go on the short list")
    for e in errs:
        print(e)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
