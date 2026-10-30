English · [中文](README_cn.md)

# naming-workflow

A workflow for naming a project, for anyone working with coding agents (Claude Code, Codex,
Antigravity): the agent fills a diamond with you (your core value, two kinds of competitors, what only
you have), looks for the space no competitor's name occupies, joins unrelated words into candidates,
checks every one for collisions, and asks you to choose once from a short list. A name passes only
when nobody **active in the same field** uses it; stars do not count.

## Install

As an [AIagents](https://github.com/musetee/aiagents) plugin (this repository is private for now):

```bash
aiagent plugin install git@github.com:musetee/naming-workflow.git
```

Without AIagents: clone it anywhere and run `bash tools/install.sh`. The skill `name-project` is then
linked into each installed agent, and `~/.naming-workflow` points to the clone. `gh` must be logged in
(`gh auth login`) for the check.

## Use it

Tell an agent "help me find a name for this project" (or "is the name X free?"). It follows
[`skills/name-project/SKILL.md`](skills/name-project/SKILL.md) and asks you only where a decision is yours.

The check also runs on its own:

```bash
python3 ~/.naming-workflow/tools/namecheck.py sousbook coherd --inspect
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
