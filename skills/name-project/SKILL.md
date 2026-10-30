---
name: name-project
description: Find a name for a project (or product, plugin, tool) that says what makes it different and that nobody active in the same field already uses - from its highlight to a metaphor, candidates, a collision check with tools/namecheck.py, a short list, and one decision by the user. Use when the user wants to name or rename a project, or asks whether a name is free.
---

# name-project: give a project a name

The steps, in order. Each ends with something the user can see; ask the user only where it says so,
one question at a time.

## 1. What the name has to say
1. Write in two sentences what the project does for whom, and **what makes it different** from the
   tools that already exist. List those tools (search the field; ask the user which ones they know).
2. Say which parts every such tool has: a name built on those does not stand out. Example: for a
   multi-agent tool, "several agents work together" is common to all of them; "you write your own
   workflows and share them" was the difference.
3. Show this to the user and let them correct it before going on. The rest builds on it.

## 2. A picture, then words
1. Look for a picture (metaphor) of the difference that people get at once, from everyday life:
   a kitchen and its recipes, a guild and its crafts, a herd and its herder. Offer two or three, with
   what each one says, and let the user pick or bring their own.
2. From the chosen picture, collect words: things in it, people in it, actions, and short
   combinations of two words (a role + its tool: "sous" + "book"). Aim for 10 to 20.
3. Leave out at once: words a known tool in the field already uses for a feature (an agent tool's
   "recipes"), and words so common they are used for something else everywhere ("cookbook" means a
   collection of code examples). Say why in one line each.

## 3. Check every candidate
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
the number of commits and the last push before you call a name taken. A project in the same field
that uses the same picture under another name is worth telling the user about, but does not take the name.

## 4. A short list, one decision
1. Show the names that passed in one table: name | what it says (in the user's words, one line) |
   what the check found. Below it, one line naming the ones left out and why
   ("active agent tool of the same name", "taken on PyPI and too common to be found").
2. Recommend one, saying why in a sentence, and say its weak point honestly (for example a word
   people may not know, which the first line of the README then has to explain).
3. Ask the user to choose, in one question (the recommended name first). If the user brings a new
   candidate instead, check it the same way and answer with what you found.

## 5. Record it
Write down where the project keeps its decisions (its plans or ledger; otherwise tell the user what
to keep): the chosen name and date, what it says, the check results with the date, the names left out
and why (so nobody checks them again), and what was learned. Before the name is used publicly,
check it once more: names get taken.

## After the decision
Renaming touches more than the repository: the README's first line, install addresses and
download links, commands, packages, links from other projects. List them for the user before changing
anything, and do it before the first public release where possible: afterwards old links and
installed copies have to be handled too.
