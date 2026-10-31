"""Tests for the wf gates of name-project (verify_steps, verify_check, verify_record) and, when the
workflow platform is next to this repository, one whole run through wf.

  python3 -m unittest discover -s tools -p 'test_*.py'
"""
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import verify_check  # noqa: E402
import verify_record  # noqa: E402
import verify_steps  # noqa: E402

NAMES = [f"name{i}" for i in range(10)]
FIELD = ["agent", "workflow"]
SINCE = "2025-10-31"


def result(name, **kw):
    r = {"name": name, "repos": 0, "exact": 0, "recent": 0, "close": [], "unclear": [], "clean": True,
         "incomplete": False, "account": "free", "pypi": "free", "npm": "free", "crates": "free"}
    r.update(kw)
    return r


def search(q="x"):
    return {"query": q, "date": "2026-10-31", "sources": ["https://example.org"], "conclusion": "nothing"}


class Fixture(unittest.TestCase):
    def setUp(self):
        self.run = Path(tempfile.mkdtemp(prefix="nw-gates-"))
        (self.run / "steps").mkdir()
        (self.run / "checks").mkdir()
        self.put("steps/1-diamond.json", {"top": ["flow", "own", "follow"], "left": ["a", "b", "c"],
                                          "right": ["d", "e", "f"], "bottom": ["any", "work", "method"],
                                          "competitors": [{"name": "x", "says": "y", "name_kind": "z"}]})
        self.put("steps/2-white-space.json", {"pattern": "p", "directions": [{"what": "craft", "why": "w"}]})
        self.put("steps/2-white-space.decision.json", {"confirm_event": 6, "values": {"chosen": "craft"}})
        self.put("steps/3-candidates.json", {"candidates": [
            {"name": n, "pair": ["flow", "craft"], "standout": "s", "confusion": "c"} for n in NAMES]})
        self.record("1", [result(n) for n in NAMES])
        self.check_doc = {"field": FIELD, "since": SINCE,
                          "candidates": {n: {"state": "checked"} for n in NAMES},
                          "proposed": [{"name": "name0", "web_plain": search(), "web_field": search(),
                                        "trademark": search()}]}
        self.put("steps/4-check.json", self.check_doc)
        self.put("steps/5-decision.json", {
            "shortlist": [{"name": "name0", "says": "s", "standout_confusion": "c", "first_letter": "n", "check": "k"}],
            "recommendation": {"name": "name0", "why": "w", "weak_point": "wp"}})
        self.put("steps/5-decision.decision.json", {"confirm_event": 20, "values": {"chosen": "name0"}})
        self.state = {"run": "r", "events": [{"n": 1, "t": "2026-10-31T10:00:00+01:00", "type": "start", "trial": True}]
                      + [{"n": i, "t": "2026-10-31T11:00:00+01:00", "type": "x"} for i in range(2, 21)]}
        self.state["events"][19]["type"] = "confirm"
        self.put(".wf/state.json", self.state)
        self.put("steps/6-record.json", {"chosen": "name0", "decision_date": "2026-10-31",
                                         "check_date": "2026-10-31", "trial": True,
                                         "left_out": [{"name": n, "reason": "not chosen"} for n in NAMES[1:]]})
        os.environ["WF_STATE"] = str(self.run / ".wf/state.json")
        os.environ.pop("WF_SNAPSHOT", None)

    def tearDown(self):
        shutil.rmtree(self.run, ignore_errors=True)
        os.environ.pop("WF_STATE", None)

    def put(self, rel, obj):
        p = self.run / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(obj))

    def record(self, n, results, inspect=False, field=FIELD, since=SINCE, started="2026-10-31T10:30:00+01:00"):
        self.put(f"checks/{n}.record.json", {"tool": "namecheck", "sha256": "0" * 64, "started_at": started,
                                             "names": [r["name"] for r in results], "field": field,
                                             "since": since, "inspect": inspect, "results": results})

    def gate(self, module, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            try:
                rc = module.main([*args, str(self.run)])
            except SystemExit as e:
                rc, _ = 1, out.write(str(e))
        return rc, out.getvalue()


class Steps(Fixture):
    def test_all_good(self):
        for sub in ("white-space", "candidates", "decision"):
            self.assertEqual(self.gate(verify_steps, sub)[0], 0, sub)

    def test_unknown_direction(self):
        self.put("steps/2-white-space.decision.json", {"confirm_event": 6, "values": {"chosen": "sea"}})
        self.assertEqual(self.gate(verify_steps, "white-space")[0], 1)

    def test_users_own_direction(self):
        self.put("steps/2-white-space.decision.json", {"confirm_event": 6, "values": {"chosen": "user:the sea"}})
        self.assertEqual(self.gate(verify_steps, "white-space")[0], 0)

    def test_pair_not_from_diamond(self):
        c = json.loads((self.run / "steps/3-candidates.json").read_text())
        c["candidates"][3]["pair"] = ["speed", "craft"]
        self.put("steps/3-candidates.json", c)
        self.assertIn("name3", self.gate(verify_steps, "candidates")[1])

    def test_shortlist_outside_proposed(self):
        d = json.loads((self.run / "steps/5-decision.json").read_text())
        d["shortlist"].append({"name": "name5", "says": "s", "standout_confusion": "c", "first_letter": "n", "check": "k"})
        self.put("steps/5-decision.json", d)
        self.assertIn("not in the proposed set", self.gate(verify_steps, "decision")[1])

    def test_user_chose_name_not_on_list(self):
        self.put("steps/5-decision.decision.json", {"confirm_event": 20, "values": {"chosen": "brandnew"}})
        self.assertIn("reopen step 3", self.gate(verify_steps, "decision")[1])


class Check(Fixture):
    def test_good(self):
        rc, out = self.gate(verify_check)
        self.assertEqual(rc, 0, out)

    def test_error_is_unresolved_not_checked(self):
        self.record("2", [result("name4", error="GitHub search failed: rate limit", clean=False)],
                    started="2026-10-31T10:40:00+01:00")
        rc, out = self.gate(verify_check)
        self.assertIn("records say unresolved/error", out)
        self.check_doc["candidates"]["name4"] = {"state": "unresolved", "reason": "error"}
        self.put("steps/4-check.json", self.check_doc)
        self.assertEqual(self.gate(verify_check)[0], 0)

    def test_unresolved_cannot_be_proposed(self):
        self.record("2", [result("name0", incomplete=True, clean=False)], started="2026-10-31T10:40:00+01:00")
        self.check_doc["candidates"]["name0"] = {"state": "unresolved", "reason": "incomplete"}
        self.put("steps/4-check.json", self.check_doc)
        self.assertIn("proposed but not checked", self.gate(verify_check)[1])

    def test_substring_is_not_the_name(self):
        self.record("1", [result(n) for n in NAMES if n != "name1"] + [result("name1x")])
        self.assertIn("name1: no namecheck record", self.gate(verify_check)[1])

    def test_missing_candidate(self):
        self.record("1", [result(n) for n in NAMES[:-1]])
        self.assertIn("name9", self.gate(verify_check)[1])

    def test_registry_unknown(self):
        self.record("2", [result("name2", npm="unknown (None)")], started="2026-10-31T10:40:00+01:00")
        self.assertIn("registry-unknown", self.gate(verify_check)[1])

    def flagged(self, **inspected):
        repo = {"fullName": "o/name3", "description": "an agent tool", "pushedAt": "2026-10-01",
                "stargazersCount": 0}
        self.record("2", [result("name3", close=[repo], clean=False)], started="2026-10-31T10:40:00+01:00")
        if inspected:
            self.record("3", [result("name3", close=[dict(repo, **inspected)], clean=False)], inspect=True,
                        started="2026-10-31T10:50:00+01:00")

    def test_not_clean_needs_inspect(self):
        self.flagged()
        self.assertIn("was not an --inspect run", self.gate(verify_check)[1])

    def test_inspect_read_false(self):
        self.flagged(read=False, error="no README")
        self.assertIn("inspect-failed", self.gate(verify_check)[1])

    def test_inspected_flagged_name_is_checked(self):
        self.flagged(read=True, commits="12", readme="an agent tool")
        rc, out = self.gate(verify_check)
        self.assertEqual(rc, 0, out)

    def test_field_differs(self):
        self.record("2", [result("name2")], field=["ai"], started="2026-10-31T10:40:00+01:00")
        self.assertIn("--field", self.gate(verify_check)[1])

    def test_since_differs(self):
        self.record("2", [result("name2")], since="2020-01-01", started="2026-10-31T10:40:00+01:00")
        self.assertIn("--since", self.gate(verify_check)[1])

    def test_other_namecheck_version(self):
        snap = self.run / ".wf/workflow/tools"
        snap.mkdir(parents=True)
        (snap / "namecheck.py").write_text("print('the snapshot copy')\n")
        os.environ["WF_SNAPSHOT"] = str(self.run / ".wf/workflow")
        try:
            self.assertIn("sha256", self.gate(verify_check)[1])
        finally:
            os.environ.pop("WF_SNAPSHOT")

    def test_search_record_incomplete(self):
        self.check_doc["proposed"][0]["trademark"] = {"query": "q", "date": "d"}
        self.put("steps/4-check.json", self.check_doc)
        out = self.gate(verify_check)[1]
        self.assertIn("trademark search lacks conclusion", out)
        self.assertIn("date (YYYY-MM-DD)", out)


class Record(Fixture):
    def test_good(self):
        rc, out = self.gate(verify_record)
        self.assertEqual(rc, 0, out)

    def edit(self, **kw):
        r = json.loads((self.run / "steps/6-record.json").read_text())
        r.update(kw)
        self.put("steps/6-record.json", r)
        return self.gate(verify_record)

    def test_wrong_chosen(self):
        self.assertIn("chosen", self.edit(chosen="name3")[1])

    def test_wrong_dates(self):
        self.assertIn("decision_date", self.edit(decision_date="2026-11-01")[1])
        self.assertIn("check_date", self.edit(decision_date="2026-10-31", check_date="2026-10-01")[1])

    def test_trial_recorded_as_formal(self):
        self.assertIn("trial", self.edit(trial=False)[1])

    def test_left_out_incomplete_or_empty_reason(self):
        self.assertIn("left_out names", self.edit(left_out=[{"name": "name1", "reason": "r"}])[1])
        lo = [{"name": n, "reason": "r"} for n in NAMES[1:]]
        lo[0]["reason"] = " "
        self.assertIn("no reason", self.edit(left_out=lo)[1])

    def test_empty_left_out_when_all_short_listed(self):
        d = json.loads((self.run / "steps/5-decision.json").read_text())
        d["shortlist"] = [{"name": n, "says": "s", "standout_confusion": "c", "first_letter": "n", "check": "k"}
                          for n in NAMES]
        self.put("steps/5-decision.json", d)
        self.assertEqual(self.edit(left_out=[])[0], 0)


class Duplicates(Fixture):
    """WP-P-001: names are compared without case and extra spaces, and counted once."""

    def cands(self, names):
        self.put("steps/3-candidates.json", {"candidates": [
            {"name": n, "pair": ["flow", "craft"], "standout": "s", "confusion": "c"} for n in names]})
        return self.gate(verify_steps, "candidates")

    def test_ten_copies_of_one_name(self):
        rc, out = self.cands(["name0"] * 10)
        self.assertEqual(rc, 1)
        self.assertIn("1 different names", out)

    def test_case_and_space_variants(self):
        rc, out = self.cands(NAMES[:9] + ["Name0 "])
        self.assertEqual(rc, 1)
        self.assertIn("the same name", out)

    def test_ten_distinct(self):
        self.assertEqual(self.cands(NAMES)[0], 0)

    def test_proposed_twice(self):
        self.check_doc["proposed"].append(dict(self.check_doc["proposed"][0], name="NAME0"))
        self.put("steps/4-check.json", self.check_doc)
        self.assertIn("proposed more than once", self.gate(verify_check)[1])

    def test_shortlist_twice(self):
        d = json.loads((self.run / "steps/5-decision.json").read_text())
        d["shortlist"].append(dict(d["shortlist"][0], name="name0 "))
        self.put("steps/5-decision.json", d)
        self.assertIn("more than once", self.gate(verify_steps, "decision")[1])

    def test_left_out_twice(self):
        r = json.loads((self.run / "steps/6-record.json").read_text())
        r["left_out"].append({"name": "name1", "reason": "again"})
        self.put("steps/6-record.json", r)
        self.assertIn("more than once", self.gate(verify_record)[1])


class Types(Fixture):
    """WP-P-002: required leaves have types and content, not only keys."""

    def test_search_fields_wrong_types(self):
        bad = {"query": 7, "date": True, "sources": [None], "conclusion": {"x": 1}}
        self.check_doc["proposed"][0].update(web_plain=bad, web_field=bad, trademark=bad)
        self.put("steps/4-check.json", self.check_doc)
        out = self.gate(verify_check)[1]
        for s in ("web_plain", "web_field", "trademark"):
            self.assertIn(f"{s} search lacks query, conclusion, date", out)

    def test_search_empty_sources(self):
        self.check_doc["proposed"][0]["web_field"]["sources"] = []
        self.put("steps/4-check.json", self.check_doc)
        self.assertIn("sources", self.gate(verify_check)[1])

    def test_record_structure(self):
        rec = json.loads((self.run / "checks/1.record.json").read_text())
        rec.update(sha256=None, started_at="later", inspect="no", names=NAMES[:9])
        self.put("checks/1.record.json", rec)
        out = self.gate(verify_check)[1]
        for word in ("sha256", "started_at", "inspect must be", "results do not match"):
            self.assertIn(word, out)

    def test_declared_state_not_allowed(self):
        self.check_doc["candidates"]["name2"] = {"state": "unresolved", "reason": "not-inspected"}
        self.put("steps/4-check.json", self.check_doc)
        self.assertIn("must say", self.gate(verify_check)[1])

    def test_left_out_reason_not_text(self):
        r = json.loads((self.run / "steps/6-record.json").read_text())
        r["left_out"][0]["reason"] = 5
        self.put("steps/6-record.json", r)
        self.assertIn("no reason", self.gate(verify_record)[1])

    def test_schema_types_in_workflow(self):
        """The step schemas give every required leaf a type (checked by wf's json gate)."""
        w = json.loads((REPO / "workflow.json").read_text())

        def leaves(schema, path):
            if schema.get("type") == "object":
                props = schema.get("properties", {})
                for k in schema.get("required", []):
                    self.assertIn(k, props, f"{path}.{k} has no type")
                    leaves(props[k], f"{path}.{k}")
            elif schema.get("type") == "array" and "items" in schema:
                leaves(schema["items"], path + "[]")
            elif path.endswith(".candidates"):
                return
            else:
                self.assertIn("type", schema, path)
        for s in w["steps"]:
            for g in s["gates"]:
                if g["type"] == "json":
                    leaves(g["schema"], s["id"])


class Inspect(Fixture):
    """WP-P-003: the latest record decides; a not-clean result needs that record to be an --inspect run."""

    repo = {"fullName": "o/name3", "description": "an agent tool", "pushedAt": "2026-10-01", "stargazersCount": 0}

    def test_old_inspect_does_not_cover_new_repo(self):
        old = dict(self.repo, fullName="old/name3", read=True, commits="1", readme="x")
        self.record("2", [result("name3", close=[old], clean=False)], inspect=True, started="2026-10-31T10:40:00+01:00")
        self.record("3", [result("name3", close=[dict(self.repo, fullName="new/name3")], clean=False)],
                    started="2026-10-31T10:50:00+01:00")
        rc, out = self.gate(verify_check)
        self.assertEqual(rc, 1)
        self.assertIn("new/name3", out)

    def test_never_inspected_cannot_be_declared_unresolved(self):
        self.record("2", [result("name3", close=[self.repo], clean=False)], started="2026-10-31T10:40:00+01:00")
        self.check_doc["candidates"]["name3"] = {"state": "unresolved", "reason": "inspect-failed"}
        self.put("steps/4-check.json", self.check_doc)
        rc, out = self.gate(verify_check)
        self.assertEqual(rc, 1)
        self.assertIn("was not an --inspect run", out)

    def test_partly_read(self):
        a = dict(self.repo, read=True, commits="1", readme="x")
        b = dict(self.repo, fullName="o2/name3", read=False, error="no README")
        self.record("2", [result("name3", close=[a, b], clean=False)], inspect=True, started="2026-10-31T10:40:00+01:00")
        self.assertIn("unresolved/inspect-failed", self.gate(verify_check)[1])
        self.check_doc["candidates"]["name3"] = {"state": "unresolved", "reason": "inspect-failed"}
        self.put("steps/4-check.json", self.check_doc)
        self.assertEqual(self.gate(verify_check)[0], 0)

    def test_inspect_attempt_failed_stays_unclear(self):
        u = dict(self.repo, description="", read=False, error="gh failed")
        self.record("2", [result("name3", unclear=[u], clean=False)], inspect=True, started="2026-10-31T10:40:00+01:00")
        self.check_doc["candidates"]["name3"] = {"state": "unresolved", "reason": "inspect-failed"}
        self.put("steps/4-check.json", self.check_doc)
        self.assertEqual(self.gate(verify_check)[0], 0)

    def test_later_clean_check_counts(self):
        self.record("2", [result("name3", close=[self.repo], clean=False)], started="2026-10-31T10:40:00+01:00")
        self.record("3", [result("name3")], started="2026-10-31T10:50:00+01:00")
        self.assertEqual(self.gate(verify_check)[0], 0)


class RecordCli(unittest.TestCase):
    """namecheck --record writes the record (network replaced by a stub)."""

    def test_round_trip(self):
        import namecheck
        tmp = Path(tempfile.mkdtemp(prefix="nw-rec-"))
        orig = namecheck.check
        namecheck.check = lambda name, since, field, do_inspect: result(name)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                namecheck.main(["alpha", "beta", "--field", "agent, workflow", "--since", SINCE,
                                "--record", str(tmp / "checks" / "1.record.json")])
        finally:
            namecheck.check = orig
        rec = json.loads((tmp / "checks" / "1.record.json").read_text())  # checks/ made by namecheck
        self.assertEqual(rec["names"], ["alpha", "beta"])
        self.assertEqual(rec["field"], ["agent", "workflow"])
        self.assertEqual(rec["since"], SINCE)
        self.assertFalse(rec["inspect"])
        self.assertEqual(rec["sha256"], __import__("hashlib").sha256((TOOLS / "namecheck.py").read_bytes()).hexdigest())
        rec["_file"] = "1.record.json"
        self.assertEqual(verify_check.record_problems(rec), [])
        shutil.rmtree(tmp)


WF = next((p / "bin" / "wf" for p in ([Path(os.environ["WF_PLATFORM"])] if os.environ.get("WF_PLATFORM") else [])
           + [REPO.parent / "durweg", Path.home() / "durweg"] if (p / "bin" / "wf").is_file()),
          REPO.parent / "durweg" / "bin" / "wf")   # the Durweg platform (wf)


@unittest.skipUnless(WF.is_file(), "workflow platform not found next to this repository")
class WholeRun(unittest.TestCase):
    """One whole run of the naming workflow through wf, with fake namecheck records (no network)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="nw-run-"))
        self.repo = self.tmp / "naming-workflow"
        shutil.copytree(REPO, self.repo, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
                   GIT_COMMITTER_EMAIL="t@t")
        for args in (["init", "-q", "-b", "main"], ["add", "-A"], ["commit", "-q", "-m", "x"]):
            subprocess.run(["git", "-C", str(self.repo), *args], check=True, env=env, capture_output=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def wf(self, *args, ok=True):
        r = subprocess.run([sys.executable, str(WF), *map(str, args)], capture_output=True, text=True)
        if ok:
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r

    def put(self, rel, obj):
        p = self.run / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(obj))

    def test_whole_run(self):
        self.wf("start", self.repo, "pilot", "--runs", self.tmp / "runs", "--trial")
        self.run = next((self.tmp / "runs").glob("*_pilot"))
        R = self.run
        self.wf("begin", R, "diamond")
        self.put("steps/1-diamond.json", {"top": ["flow", "own", "follow"], "left": ["a", "b", "c"],
                                          "right": ["d", "e", "f"], "bottom": ["any", "work", "method"],
                                          "competitors": [{"name": "x", "says": "y", "name_kind": "z"}]})
        self.wf("propose", R, "diamond")
        self.wf("confirm", R, "diamond", "--quote", "yes")
        self.wf("done", R, "diamond")
        self.wf("begin", R, "white-space")
        self.put("steps/2-white-space.json", {"pattern": "p", "directions": [{"what": "craft", "why": "w"}]})
        self.wf("propose", R, "white-space")
        self.wf("confirm", R, "white-space", "--quote", "craft", "--set", "chosen=craft")
        self.wf("done", R, "white-space")
        self.wf("begin", R, "candidates")
        self.put("steps/3-candidates.json", {"candidates": [
            {"name": n, "pair": ["flow", "craft"], "standout": "s", "confusion": "c"} for n in NAMES]})
        self.wf("done", R, "candidates")
        self.wf("begin", R, "check")
        sha = __import__("hashlib").sha256((self.repo / "tools/namecheck.py").read_bytes()).hexdigest()
        self.put("checks/1.record.json", {"tool": "namecheck", "sha256": sha, "started_at": "2026-10-31T10:30:00+01:00",
                                          "names": NAMES, "field": FIELD, "since": SINCE, "inspect": False,
                                          "results": [result(n) for n in NAMES]})
        self.put("steps/4-check.json", {"field": FIELD, "since": SINCE,
                                        "candidates": {n: {"state": "checked"} for n in NAMES},
                                        "proposed": [{"name": "name0", "web_plain": search(), "web_field": search(),
                                                      "trademark": search()}]})
        self.wf("done", R, "check")
        self.wf("begin", R, "decision")
        self.put("steps/5-decision.json", {
            "shortlist": [{"name": "name0", "says": "s", "standout_confusion": "c", "first_letter": "n", "check": "k"}],
            "recommendation": {"name": "name0", "why": "w", "weak_point": "wp"}})
        self.wf("propose", R, "decision")
        self.wf("confirm", R, "decision", "--quote", "name0", "--set", "chosen=name0")
        self.wf("done", R, "decision")
        self.wf("begin", R, "record")
        state = json.loads((R / ".wf/state.json").read_text())
        confirm_day = [e for e in state["events"] if e["type"] == "confirm"][-1]["t"][:10]
        self.put("steps/6-record.json", {"chosen": "name0", "decision_date": confirm_day, "check_date": "2026-10-31",
                                         "trial": True, "left_out": [{"name": n, "reason": "r"} for n in NAMES[1:]]})
        self.wf("done", R, "record")
        r = self.wf("check", R)
        self.assertIn("PASS", r.stdout)


if __name__ == "__main__":
    unittest.main()
