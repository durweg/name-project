# Changelog

## Unreleased: renamed to name-project

The repository, plugin and folder link take the workflow's name: `naming-workflow` ->
`name-project` (GitHub `musetee/name-project`), `~/.naming-workflow` -> `~/.name-project`.
`tools/install.sh` re-points links of a clone under either name and removes an old
`~/.naming-workflow` link that points at one; a link of that name to anything else stays.

## Unreleased: the command is `durweg`

The workflow platform's command `wf` was renamed `durweg` with no alias, so the skill's
`wf start/begin/done/propose/confirm/reopen` no longer ran. Skill, README and gate docstrings now say
`durweg`; `tools/test_wf_gates.py` looks for `bin/durweg`: its whole-run test had been skipped
since the rename ("workflow platform not found") and runs again. `{wf}` in `workflow.json` is
Durweg's own placeholder for the snapshot and stays.

## Unreleased: runs with wf

`workflow.json` describes the six steps for the workflow platform's `wf`: each step writes fixed
files under `steps/` and passes gates before the next one starts (`tools/verify_steps.py`,
`verify_check.py`, `verify_record.py`; a name counts as checked only when a namecheck record shows a
complete result, inspected when it is not clean). `namecheck.py --record FILE` saves the results
with the names, `--field`, `--since`, start time and the script's sha256. The method of the skill is
unchanged; each step now ends with the files it writes.

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
