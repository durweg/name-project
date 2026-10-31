# Changelog

## 2026-10-31: web and trademark search before the short list

Step 4 now also asks for a web search and a trademark search of each name before it goes on the
short list: namecheck.py sees only GitHub and the package sites (Methodkit was CLEAN there and is a
registered trademark).

## 2026-10-31: method rewritten

The way to find candidates is replaced by the user's chosen rules (`namingrules.txt`, not in the
repository): the diamond exercise (core value, two kinds of competitors, the difference; nouns and
verbs only), the white space no competitor's name occupies, forced association of unrelated words
(Windsurf), and the sound of the first letter as a hint on the short list, never a filter. The
everyday-picture step of the first version is gone. The collision check is kept as it was.

## 2026-10-31: first version

The method used to rename AIagents (2026-10-30/31), written down as a workflow: skill `name-project`
(highlight → picture → candidates → check → short list → one decision → record), `tools/namecheck.py`
(GitHub repositories by activity and field, GitHub account, PyPI, npm, crates.io; a same-name active
repository without a description is CHECK until its README is read), installer for Claude Code, Codex
and Antigravity, tests without network.
