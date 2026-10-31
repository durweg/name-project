English · [中文](README_cn.md)

# name-project

**A [Durweg](https://github.com/musetee/durweg) workflow that has AI agents (Claude Code, Codex, Antigravity) find a name for your project in 6 fixed steps, so that the name says what is special about it and nobody active in the same field already uses it.**

The agent fills a diamond with you (your core value, two kinds of competitors, what only you have),
looks for the space no competitor's name occupies, joins unrelated words into candidates, checks every
one for collisions, and asks you to choose once from a short list. A name passes only when nobody
**active in the same field** uses it; stars do not count. Durweg itself was named with it.

A real example, step by step: **[naming stepaper](https://claude.ai/artifact/CKh1BGrRvUDbokrhLAi58t)** (English, with a switch to Chinese; a copy is in this repository: [case/stepaper-naming.html](case/stepaper-naming.html)).

## 🧭 Install

You need Durweg first ([install Durweg](https://github.com/musetee/durweg/blob/main/README.md)). The
collision check searches GitHub, so you also need a GitHub account and the GitHub command line `gh`,
logged in once with `gh auth login`.

1. **Open a terminal** (as in step 1 of Durweg's "Every day").
2. **Add it to your library:** `durweg library add https://github.com/musetee/name-project.git --name name-project`.
   It downloads the workflow to `~/Durweg/workflows/name-project/` and registers it. This needs git;
   without git, click **Code → Download ZIP** on GitHub, unzip it to a folder and run
   `durweg library add <that folder> --name name-project`.

Done looks like this: it prints `added name-project`, and `durweg library list` lists `name-project`.

## 📅 Use it

Start your agent in the folder of the project you want to name and tell it: "Run name-project with durweg."

## 🪜 The 6 steps

| # | Step | Delivers | You decide |
| :--- | :--- | :--- | :---: |
| 1 | The diamond | Your core value, two kinds of competitors and what only you have, as nouns and verbs | ✅ |
| 2 | The white space | The direction no competitor's name takes | ✅ |
| 3 | Forced association | 10 to 20 candidate names | |
| 4 | Check every candidate | GitHub, PyPI, npm, crates.io, web and trademark search for each name | |
| 5 | A short list, one decision | A few names with a recommendation; you choose once | ✅ |
| 6 | Record it | The chosen name and why, with the checks behind it | |

## 🙋 I want to …

| I want to | How |
| :--- | :--- |
| See a whole run, from the diamond to the decision | [Case: naming stepaper](https://claude.ai/artifact/CKh1BGrRvUDbokrhLAi58t) |
| Only check whether a name is free | See [Check a name on its own](#-check-a-name-on-its-own) below |
| Make it my own | Make your own version with Durweg's write-your-method, or edit `workflow.json` and `skills/name-project/SKILL.md` following the [workflow format](https://github.com/musetee/durweg/blob/main/docs/workflow-format.md) |
| Stop using it | `durweg library remove name-project`, then delete `~/Durweg/workflows/name-project/` |

## 🔍 Check a name on its own

```bash
python3 ~/Durweg/workflows/name-project/tools/namecheck.py sousbook coherd --inspect
```

```text
sousbook       CLEAN  repos 0 (same name 0, updated since 2025-10-31: 0)  account free  pypi free  npm free  crates free
coherd         TAKEN  repos 2 (same name 1, updated since 2025-10-31: 1)  account free  pypi free  npm free  crates free
    ! ye-c/coherd 0* pushed 2026-10-30:
      100+ commits, Python, created 2026-08-13: # coherd coherd 把多个 AI agent 组织成一个小团队 …
```

`CLEAN`: no repository updated in the last year describes itself with a word of your field
(`--field`, default: agent, ai, llm, workflow, …). `TAKEN`: one does (`!`). `CHECK`: a same-name
repository updated in the last year has no description (`?`); run again with `--inspect`, which reads
its README. Always read the `!` lines before calling a name taken.

Tests: `python3 -m unittest discover -s tools -p 'test_*.py'` (no network).

---

License: [MIT](LICENSE).
