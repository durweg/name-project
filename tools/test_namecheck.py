"""Tests without network: how namecheck judges names (cases met while naming AIagents, 2026-10-30/31),
and the installer in a temporary HOME."""
import importlib.util
import os
import shutil
import subprocess
import tempfile
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


class Install(unittest.TestCase):
    def test_links_the_skill_for_installed_agents_and_removes_only_its_own(self):
        home = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, home)
        (home / ".claude").mkdir()
        (home / ".codex").mkdir()
        env = dict(os.environ, HOME=str(home))
        env.pop("CODEX_HOME", None)
        for _ in range(2):
            out = subprocess.run(["bash", str(ROOT / "tools/install.sh")], env=env, capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        target = (ROOT / "skills/name-project").resolve()
        self.assertEqual((home / ".claude/skills/name-project").resolve(), target)
        self.assertEqual((home / ".codex/skills/name-project").resolve(), target)
        self.assertFalse((home / ".gemini").exists())            # Antigravity not installed: not touched
        self.assertTrue((home / ".naming-workflow/skills/name-project/SKILL.md").exists())
        (home / ".claude/skills/mine").mkdir()
        subprocess.run(["bash", str(ROOT / "tools/install.sh"), "--remove"], env=env, check=True, capture_output=True)
        self.assertFalse((home / ".claude/skills/name-project").exists())
        self.assertFalse((home / ".naming-workflow").exists())
        self.assertTrue((home / ".claude/skills/mine").exists())


if __name__ == "__main__":
    unittest.main()
