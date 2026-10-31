---
name: name-project
description: Find a name for a project (or product, plugin, tool) with the diamond exercise - core value, two kinds of competitors and the difference, as nouns and verbs - then the white space nobody in the market uses, forced associations of unrelated words, a collision check with tools/namecheck.py, a short list, and one decision by the user. Use when the user wants to name or rename a project, or asks whether a name is free.
---

# name-project: give a project a name

The steps, in order. Each ends with something the user can see; ask the user only where it says so,
one question at a time.


**Run it with wf** (skill run-workflow): `wf start ~/.naming-workflow <slug> --runs <project>/runs`,
then for each step `wf begin`, write the step's files (named at the end of each step below, paths
relative to the run folder), and `wf done`. Where the user decides, `wf propose` before showing it
and `wf confirm --quote "<their words>" --set chosen=<…>` after they answer. Without wf, follow the
same steps and keep the same files.

## 1. The diamond
Draw a diamond with four corners and fill each with **3 to 5 nouns or verbs, no adjectives**
("speed", "connect", "flow", not "fast", "connected"):
- **top**: the project's core value, what it gives its user;
- **left**: how the main competitors present themselves;
- **right**: how another kind of competitor presents itself (a different category that solves the
  same need, for example a manual practice or a general-purpose tool);
- **bottom**: what only this project has.

Find the competitors first: search the field and ask the user which ones they know. For the left and
right corners, use the words the competitors use about themselves (their names, first lines,
taglines), not your summary of them. Write down the competitors' **names** too, and what kind of
names they are (technical terms, people's roles, made-up words, ...).

Show the diamond to the user and let them correct it before going on. The rest builds on it.

**Files:** `steps/1-diamond.json`: `{"top": [3-5 words], "left": [...], "right": [...], "bottom": [...],
"competitors": [{"name", "says" (their own words), "name_kind"}]}`. Propose it, show it, confirm when
the user agrees with the version shown (after a correction: change it, propose again, show it again).

## 2. The white space
1. Look at which words and kinds of names the competitors already occupy. Name the pattern in one
   line, for example "they are all technical role names: Copilot, Codex".
2. Look for combinations of the top and bottom words that **no competitor uses**, above all ones
   that could stand for a new category instead of a better member of the old one.
3. Choose one or two directions that leave the competitors' pattern behind: if they are all
   technical, a direction from nature, motion, craft or the senses. Show them to the user in one
   line each (what the direction is, why it stands apart) and let the user pick or bring their own.

**Files:** `steps/2-white-space.json`: `{"pattern": "one line", "directions": [{"what", "why"}] (1-2)}`.
Propose, show, and confirm with `--set chosen=<the direction's what>`, or `--set chosen=user:<their
words>` when the user brings their own.

## 3. Forced association: candidates
1. Connect words that seem unrelated: one from the top or bottom corner (what the project does or has
   alone) with one from the chosen direction. Example: Wind + Surf = Windsurf, the picture of moving
   freely over a sea of code, chosen when the market was full of technical names.
2. Build candidates from these pairs: whole words joined, parts of words (Vercel = V + "cel" from
   accelerate), or one word that carries the picture alone. Aim for 10 to 20.
3. Do not drop a candidate for the kind of word in it. Instead write one line per candidate on how
   it stands out and what it could be confused with, judged on the whole combination: does it read like
   the competitors' names from step 2, does a known tool in the field use one of its words for a
   feature, is it so common that people will not find it. A common or familiar word in a new
   combination can still be a new name; whether it is taken is settled by the check in step 4.

**Files:** `steps/3-candidates.json`: `{"candidates": [{"name", "pair": [word from top or bottom,
word from the direction], "standout", "confusion"}]}`, 10 to 20, names unique.

## 4. Check every candidate
Run `python3 ~/.naming-workflow/tools/namecheck.py <names...> --field <words of the field>`
(needs `gh` logged in; it pauses between names because GitHub limits searches). Then, for every name
that is not CLEAN, run it again with `--inspect` and read what it prints. For each name it reports:
- GitHub repositories with the name, how many were updated in the last year, and those whose
  description is in the field (`!`); a same-name repository updated in the last year with no
  description is `?` until `--inspect` has read its README;
- whether a GitHub account of that name exists (it matters only for an organisation of that name);
- PyPI, npm and crates.io.

Judge by **activity and field, never by stars**: a new project updated this week in the same field
takes the name even with 0 stars; an empty template untouched for a year does not. Look at the README,
the number of commits and the last push before you call a name taken.

namecheck.py does not see products outside these sites. Before a name goes on the short list, search
the web for it, with and without words of the field, and for a registered trademark of that name: a
name free on GitHub can still be a sold product or brand for the same users (Methodkit was CLEAN on
GitHub and is the MethodKit® trademark).

**Files:** run namecheck from the project folder (not inside the run folder) with
`--record <run>/checks/<n>.record.json` every time (the plain check of all
candidates, and `--inspect` for every name that is not CLEAN), with the same `--field` and `--since`
in all of them. Then `steps/4-check.json`:
`{"field": [the field words], "since": "YYYY-MM-DD", "candidates": {"<name>": {"state": "checked"}
or {"state": "unresolved", "reason": "error|incomplete|registry-unknown|inspect-failed|not-inspected"}},
"proposed": [{"name", "web_plain", "web_field", "trademark"}]}`, where each of the three searches is
`{"query", "date", "sources": [...], "conclusion"}`. Write the state the records show (the gate
recomputes it); only checked names can be proposed. The short list of step 5 comes from `proposed`.

## 5. A short list, one decision
1. Show the names that passed in one table: name | the pair it comes from and what it says (one line)
   | how it stands out and its confusion risk (from step 3) | sound of the first letter | what the
   check found. Below it, one line naming the ones the check left out and why ("active agent tool of
   the same name", "taken on PyPI by an active package in the field").
2. The sound column is **a hint, not a filter**: say whether the first letter's feel fits the top
   corner, and use it only to choose between names that are otherwise even. Feels often named:
   B steady and trustworthy; V speed and vitality; S smooth and elegant; X precise and technical, but
   it can feel cold. Do not drop a name for its letter.
3. Recommend one, saying why in a sentence, and say its weak point honestly (for example a word
   people may not know, which the first line of the README then has to explain).
4. Ask the user to choose, in one question (the recommended name first). If the user brings a new
   candidate instead, check it the same way and answer with what you found.

**Files:** `steps/5-decision.json`: `{"shortlist": [{"name", "says", "standout_confusion",
"first_letter", "check"}], "recommendation": {"name", "why", "weak_point"}}`; every name on the short
list from `proposed` of step 4. Propose, ask, and confirm with `--set chosen=<name>`. A name the user
brings that is not on the list: `wf reopen <run> candidates --reason "user proposes <name>"`, add
it, check it in step 4, then come back.

## 6. Record it
Write down where the project keeps its decisions (its plans or ledger; otherwise tell the user what
to keep): the diamond, the chosen direction, the chosen name and date, the check results with the
date, and the names left out and why (so nobody checks them again). Before the name is used publicly,
check it once more: names get taken.

**Files:** `steps/6-record.json`: `{"chosen", "decision_date" (the day the user chose),
"check_date" (the day of the latest check), "trial": true|false (as the run was started),
"left_out": [{"name", "reason"}] (every candidate not on the short list; empty if none)}`. In a trial
run the choice is a trial choice, not the project's decision.

## After the decision
Renaming touches more than the repository: the README's first line, install addresses and
download links, commands, packages, links from other projects. List them for the user before changing
anything, and do it before the first public release where possible: afterwards old links and
installed copies have to be handled too.
