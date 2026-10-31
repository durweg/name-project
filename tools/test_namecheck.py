"""Tests without network: how namecheck judges names (cases met while naming AIagents, 2026-10-30/31),
and the installer in a temporary HOME."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("namecheck", ROOT / "tools/namecheck.py")
nc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nc)
FIELD = nc.DEFAULT_FIELD.split(",")
SINCE = "2025-10-31"


def repo(full, desc, pushed, stars=0):
    return {"fullName": full, "description": desc, "pushedAt": pushed, "stargazersCount": stars}


class Judging(unittest.TestCase):
    def test_an_active_project_in_the_field_takes_the_name_whatever_its_stars(self):
        r = nc.classify("workways", [repo("noahjohnson0/workways", "Workways: agentic workflows, skills, and methods for AI coding agents", "2026-10-30")], SINCE, FIELD)
        self.assertFalse(r["clean"])
        self.assertEqual(r["close"][0]["fullName"], "noahjohnson0/workways")

    def test_an_old_empty_template_does_not(self):
        r = nc.classify("oxherd", [repo("jaybuidl/oxherd", None, "2025-02-28")], SINCE, FIELD)
        self.assertTrue(r["clean"])

    def test_an_active_same_name_repository_without_description_must_be_looked_at(self):
        # ye-c/coherd: active, same field, but no description; only its README tells.
        r = nc.classify("coherd", [repo("ye-c/coherd", None, "2026-10-30"),
                                   repo("EthanCoherd/EthanCoherd", "Config files for my GitHub profile.", "2021-03-17")], SINCE, FIELD)
        self.assertFalse(r["clean"])
        self.assertEqual([u["fullName"] for u in r["unclear"]], ["ye-c/coherd"])
        self.assertEqual(r["close"], [])

    def test_active_projects_outside_the_field_do_not(self):
        r = nc.classify("waymark", [repo("suruthi054/waymark-desktop", "Floating Minimap, Farming Routes and Collection Tracking for AION 2", "2026-10-30", 58)], SINCE, FIELD)
        self.assertTrue(r["clean"])

    def test_field_words_are_whole_words(self):
        self.assertTrue(nc.in_field("AI-powered planner", ["ai"]))
        self.assertTrue(nc.in_field("A multi-agent team", ["agent"]))
        self.assertFalse(nc.in_field("He said hello", ["ai"]))
        self.assertFalse(nc.in_field(None, ["ai"]))

    def test_a_readme_in_the_field_turns_unclear_into_taken(self):
        calls = {}
        def fake_gh(args):
            calls.setdefault("n", 0)
            if args[:2] == ["search", "repos"]:
                return [repo("ye-c/coherd", None, "2026-10-30")]
            if args[1] == "users/coherd":
                return None
            if args[1].endswith("/readme"):
                import base64
                return {"content": base64.b64encode("coherd 把多个 AI agent 组织成一个小团队".encode()).decode()}
            if args[1].endswith("/commits?per_page=100"):
                return [{}] * 100
            return {"language": "Python", "created_at": "2026-08-13T00:00:00Z"}
        real_gh, real_http = nc.gh_json, nc.http_status
        nc.gh_json, nc.http_status = fake_gh, lambda url: 404
        try:
            r = nc.check("coherd", SINCE, FIELD, do_inspect=True)
        finally:
            nc.gh_json, nc.http_status = real_gh, real_http
        self.assertFalse(r["clean"])
        self.assertEqual(r["close"][0]["commits"], "100+")
        self.assertEqual((r["account"], r["pypi"], r["npm"], r["crates"]), ("free", "free", "free", "free"))


class Failures(unittest.TestCase):
    """A failed or partial look must never read as "free" (NW-R)."""

    def run_check(self, fake, http=lambda url: 404, inspect_=False):
        real_gh, real_http = nc.gh_json, nc.http_status
        nc.gh_json, nc.http_status = fake, http
        try:
            return nc.check("demo", SINCE, FIELD, do_inspect=inspect_)
        finally:
            nc.gh_json, nc.http_status = real_gh, real_http

    def test_a_failed_search_is_an_error_not_a_clean_name(self):
        def fake(args):
            raise nc.GhError("HTTP 403: API rate limit exceeded")
        r = self.run_check(fake)
        self.assertFalse(r["clean"])
        self.assertIn("rate limit", r["error"])

    def test_a_failed_account_look_is_unknown_not_free(self):
        def fake(args):
            if args[0] == "search":
                return []
            raise nc.GhError("gh: not logged in")
        r = self.run_check(fake)
        self.assertTrue(r["account"].startswith("unknown"))

    def test_a_full_page_of_results_is_incomplete(self):
        many = [repo(f"u{i}/demo-{i}", "a recipe app", "2020-01-01") for i in range(nc.LIMIT)]
        r = self.run_check(lambda args: many if args[0] == "search" else None)
        self.assertTrue(r["incomplete"])
        self.assertFalse(r["clean"])

    def test_an_unreadable_readme_keeps_the_name_unclear(self):
        def fake(args):
            if args[0] == "search":
                return [repo("x/demo", None, "2026-10-30")]
            if args[1] == "users/demo":
                return None
            raise nc.GhError("HTTP 502")
        r = self.run_check(fake, inspect_=True)
        self.assertFalse(r["clean"])
        self.assertEqual([u["fullName"] for u in r["unclear"]], ["x/demo"])

    def readme_case(self, readme):
        def fake(args):
            if args[0] == "search":
                return [repo("x/demo", None, "2026-10-30")]
            if args[1] == "users/demo":
                return None
            if args[1].endswith("/readme"):
                return readme
            if args[1].endswith("/commits?per_page=100"):
                return [{}] * 3
            return {"language": "Go", "created_at": "2026-01-01T00:00:00Z"}
        return self.run_check(fake, inspect_=True)

    def test_no_readme_is_no_evidence(self):
        r = self.readme_case(None)                                  # GitHub: 404, no README
        self.assertFalse(r["clean"])
        self.assertEqual(r["unclear"][0]["error"], "it has no README to judge by")

    def test_an_empty_readme_is_no_evidence(self):
        r = self.readme_case({"content": ""})
        self.assertFalse(r["clean"])
        self.assertEqual(r["unclear"][0]["error"], "its README is empty")

    def test_the_whole_readme_is_judged_not_only_its_start(self):
        import base64
        text = "# demo\n" + "word " * 80 + "\nAn orchestrator for AI agents."
        def fake(args):
            if args[0] == "search":
                return [repo("x/demo", None, "2026-10-30")]
            if args[1] == "users/demo":
                return None
            if args[1].endswith("/readme"):
                return {"content": base64.b64encode(text.encode()).decode()}
            if args[1].endswith("/commits?per_page=100"):
                return [{}] * 3
            return {"language": "Go", "created_at": "2026-01-01T00:00:00Z"}
        r = self.run_check(fake, inspect_=True)
        self.assertEqual([c["fullName"] for c in r["close"]], ["x/demo"])
        self.assertNotIn("readme_text", r["close"][0])


if __name__ == "__main__":
    unittest.main()
