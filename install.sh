#!/bin/sh
# Install the Motus CLI and deploy plugins for detected coding agents.
# Usage: curl -fsSL https://raw.githubusercontent.com/lithos-ai/motus/main/install.sh | sh
set -eu

echo "Installing motus..." >&2

# -- Install CLI ---------------------------------------------------------------

if ! command -v uv >/dev/null 2>&1
then
	echo "Installing uv..." >&2
	curl -LsSf https://astral.sh/uv/install.sh | sh
	export PATH="$HOME/.local/bin:$PATH"
fi

if uv tool list 2>/dev/null | grep -q lithosai-motus
then
	uv tool upgrade lithosai-motus
else
	uv tool install lithosai-motus
fi

# Resolve the installed plugin path
plugin_dir="$(python3 -c "from pathlib import Path; import motus; print(Path(motus.__file__).parent / 'plugins' / 'motus')")"

# -- Deploy plugins for detected agents ----------------------------------------

installed=""
skipped=""

add_installed() { installed="${installed:+$installed, }$1"; }
add_skipped()   { skipped="${skipped:+$skipped, }$1"; }

# Claude Code — marketplace from GitHub, auto-updates independently
if command -v claude >/dev/null 2>&1
then
	claude plugin marketplace add lithos-ai/motus 2>/dev/null || true
	claude plugin install motus@LithosAI 2>/dev/null || true
	python3 -m motus.enable_claude_auto_update
	add_installed "Claude Code"
else
	add_skipped "Claude Code"
fi

# Codex — symlink skill only (full plugin causes duplicate registration)
if [ -d "$HOME/.codex" ]
then
	mkdir -p "$HOME/.codex/skills"
	rm -rf "$HOME/.codex/skills/motus"
	ln -s "$plugin_dir/skills/motus" "$HOME/.codex/skills/motus"
	add_installed "Codex"
else
	add_skipped "Codex"
fi

# Cursor — symlink skill only (full plugin causes duplicate registration)
if [ -d "$HOME/Library/Application Support/Cursor" ] || \
    [ -d "$HOME/.config/Cursor" ]
then
	mkdir -p "$HOME/.cursor/skills"
	rm -rf "$HOME/.cursor/skills/motus"
	ln -s "$plugin_dir/skills/motus" "$HOME/.cursor/skills/motus"
	add_installed "Cursor"
else
	add_skipped "Cursor"
fi

# Gemini — extension (uses EXTENSIONS.md, not SKILL.md)
if command -v gemini >/dev/null 2>&1 || [ -d "$HOME/.gemini" ]; then
	mkdir -p "$HOME/.gemini/extensions"
	rm -rf "$HOME/.gemini/extensions/motus"
	ln -s "$plugin_dir/skills/motus" "$HOME/.gemini/extensions/motus"
	add_installed "Gemini"
else
	add_skipped "Gemini"
fi

# -- Report --------------------------------------------------------------------

[ -n "$installed" ] && echo "Installed motus plugin for: $installed"
[ -n "$skipped" ]   && echo "Skipped (not detected): $skipped"
[ -n "$installed" ] && echo "Done. Restart your coding agent to pick up the /motus skill."
