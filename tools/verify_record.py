#!/usr/bin/env python3
"""wf gate for step 6 of name-project (design WP-R-014): the record agrees with the earlier steps.

  verify_record.py RUN

steps/6-record.json must say: chosen = the name the user chose in step 5; decision_date = the date
of step 5's confirm event; check_date = the latest start date of the namecheck records; trial = the
run's --trial flag; left_out = exactly the candidates not on the short list, each with a reason
(an empty list when there are none). Reads the run's event log through $WF_STATE.

Exit 1 with one line per problem. Standard library only (wf snapshot rule).
"""
import json
import os
import sys
from pathlib import Path


def load(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        sys.exit(f"cannot read {p}: {e}")


def key(name):
    return " ".join(str(name).split()).lower()


def main(argv):
    if len(argv) != 1:
        sys.exit(__doc__)
    run = Path(argv[0])
    state = load(os.environ.get("WF_STATE") or run / ".wf/state.json")
    events = {e["n"]: e for e in state["events"]}
    rec = load(run / "steps/6-record.json")
    dec5 = load(run / "steps/5-decision.decision.json")
    errs = []

    chosen = (dec5.get("values") or {}).get("chosen", "")
    if key(rec.get("chosen", "")) != key(chosen):
        errs.append(f"chosen {rec.get('chosen')!r}, but the user chose {chosen!r} in step 5")

    confirm = events.get(dec5.get("confirm_event"))
    want = (confirm or {}).get("t", "")[:10]
    if rec.get("decision_date") != want:
        errs.append(f"decision_date {rec.get('decision_date')!r}, the user confirmed on {want!r}")

    starts = [load(p).get("started_at", "")[:10] for p in (run / "checks").glob("*.record.json")]
    want = max(starts) if starts else ""
    if rec.get("check_date") != want:
        errs.append(f"check_date {rec.get('check_date')!r}, the latest check started on {want!r}")

    trial = bool(state["events"][0].get("trial"))
    if rec.get("trial") is not trial:
        errs.append(f"trial is {rec.get('trial')!r}, but this run was started with trial={trial}")

    cands = {key(c.get("name")) for c in load(run / "steps/3-candidates.json").get("candidates", [])}
    short = {key(s.get("name")) for s in load(run / "steps/5-decision.json").get("shortlist", [])}
    left = rec.get("left_out")
    if not isinstance(left, list):
        errs.append("left_out must be a list")
        left = []
    names = [key(x.get("name", "")) for x in left]
    if sorted(names) != sorted(cands - short):
        errs.append(f"left_out names {sorted(names)} should be exactly the candidates not on the short "
                    f"list {sorted(cands - short)}")
    for x in left:
        if not str(x.get("reason", "")).strip():
            errs.append(f"left_out {x.get('name')}: no reason")
    for e in errs:
        print(e)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
