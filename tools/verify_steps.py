#!/usr/bin/env python3
"""Durweg gate for steps 2, 3 and 5 of name-project: the links between steps that a JSON schema cannot
express. Run by durweg from the run's snapshot:

  verify_steps.py white-space RUN   the user's chosen direction is one of the directions (or their own)
  verify_steps.py candidates RUN    each candidate's pair starts with a word of the diamond's top or bottom
  verify_steps.py decision RUN      short list within the proposed set, recommendation and choice in it

Exit 1 with one line per problem. Standard library only, no other local files (Durweg snapshot rule).
"""
import json
import sys
from pathlib import Path


def load(run, rel):
    try:
        return json.loads((run / rel).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        sys.exit(f"cannot read {rel}: {e}")


def chosen(run, rel):
    return (load(run, rel).get("values") or {}).get("chosen", "")


def low(s):
    return " ".join(str(s).split()).lower()


def white_space(run):
    ws = load(run, "steps/2-white-space.json")
    c = chosen(run, "steps/2-white-space.decision.json")
    whats = [low(d.get("what", "")) for d in ws.get("directions", [])]
    if not c.strip():
        return ["no chosen direction: confirm with --set chosen=<direction>"]
    if c.startswith("user:") and c[5:].strip():
        return []
    if low(c) not in whats:
        return [f"chosen direction {c!r} is not one of the directions {whats}; "
                f"a direction the user brings is recorded as chosen=user:<their words>"]
    return []


def candidates(run):
    d = load(run, "steps/1-diamond.json")
    words = {low(w) for w in d.get("top", []) + d.get("bottom", [])}
    errs, seen = [], {}
    cands = load(run, "steps/3-candidates.json").get("candidates", [])
    for c in cands:
        k = low(c.get("name", ""))
        if k in seen:
            errs.append(f"{c.get('name')!r}: the same name as {seen[k]!r} (names are compared without case "
                        f"and extra spaces)")
        seen.setdefault(k, c.get("name"))
    if len(seen) < 10:
        errs.append(f"{len(seen)} different names; step 3 needs 10 to 20")
    for c in cands:
        pair = c.get("pair") or []
        if len(pair) != 2:
            errs.append(f"{c.get('name')}: pair must be two words")
        elif low(pair[0]) not in words:
            errs.append(f"{c.get('name')}: {pair[0]!r} is not a word of the diamond's top or bottom")
    return errs


def decision(run):
    proposed = {low(p.get("name", "")) for p in load(run, "steps/4-check.json").get("proposed", [])}
    dec = load(run, "steps/5-decision.json")
    short = [low(s.get("name", "")) for s in dec.get("shortlist", [])]
    dup = sorted({s for s in short if short.count(s) > 1})
    errs_dup = [f"{d!r} is on the short list more than once" for d in dup]
    errs = errs_dup + [f"{s!r} is on the short list but not in the proposed set of step 4; "
                       f"reopen step 3 to add a new name" for s in short if s not in proposed]
    rec = low((dec.get("recommendation") or {}).get("name", ""))
    if rec not in short:
        errs.append(f"the recommendation {rec!r} is not on the short list")
    c = low(chosen(run, "steps/5-decision.decision.json"))
    if not c:
        errs.append("no chosen name: confirm with --set chosen=<name>")
    elif c not in short:
        errs.append(f"the user chose {c!r}, which is not on the short list: reopen step 3, add it as a "
                    f"candidate and check it")
    return errs


def main(argv):
    if len(argv) != 2 or argv[0] not in ("white-space", "candidates", "decision"):
        sys.exit(__doc__)
    errs = {"white-space": white_space, "candidates": candidates, "decision": decision}[argv[0]](Path(argv[1]))
    for e in errs:
        print(e)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
