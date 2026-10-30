#!/usr/bin/env bash
# Install naming-workflow on this computer, wherever it was cloned:
#   bash tools/install.sh            link ~/.naming-workflow -> this clone, and the skill name-project
#                                    into each agent's skill folder
#   bash tools/install.sh --remove   remove the links this script made (used by `aiagent plugin
#                                    disable` / `remove`)
# Claude Code reads ~/.claude/skills/<name>/SKILL.md, Codex ${CODEX_HOME:-~/.codex}/skills,
# Antigravity ~/.gemini/config/skills. Links, not copies, so `git pull` here updates every agent.
# A real file or folder in the way is left alone and reported.
set -euo pipefail
NW="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
remove=''
[ "${1:-}" = "--remove" ] && remove=1
[ -z "${1:-}" ] || [ -n "$remove" ] || { echo "usage: bash tools/install.sh [--remove]"; exit 2; }

ours() {   # ours <link target>: an earlier clone of naming-workflow (moved), or its skill folder
    local target="${1%/}" root
    case "$target" in */skills/name-project) root="${target%/skills/name-project}" ;; *) root="$target" ;; esac
    grep -qs '"name": "naming-workflow"' "$root/aiagent-plugin.json"
}

link() {   # link <target> <link path>
    local src="$1" dst="$2"
    if [ -n "$remove" ]; then
        if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then rm "$dst"; echo "[OK] removed $dst"; fi
        return 0
    fi
    mkdir -p "$(dirname "$dst")"
    if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then echo "[OK] $dst (already linked)"
    elif [ -L "$dst" ] && ours "$(readlink "$dst")"; then ln -sfn "$src" "$dst"; echo "[OK] $dst -> $src (re-pointed from an earlier clone)"
    elif [ -L "$dst" ]; then echo "[!]  $dst points to $(readlink "$dst"), not to naming-workflow; left unchanged"
    elif [ -e "$dst" ]; then echo "[!]  $dst exists and is not a link; left unchanged"
    else ln -s "$src" "$dst"; echo "[OK] $dst -> $src"; fi
}

link "$NW" "$HOME/.naming-workflow"
for dir in "$HOME/.claude/skills" "${CODEX_HOME:-$HOME/.codex}/skills" "$HOME/.gemini/config/skills"; do
    [ -d "$(dirname "$dir")" ] || continue          # that agent is not installed
    link "$NW/skills/name-project" "$dir/name-project"
done
