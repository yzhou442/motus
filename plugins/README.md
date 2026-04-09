# Plugin Packaging Design

## Requirements

1. **One-command install** on macOS and Linux: `curl -fsSL .../install.sh | sh`
2. **Four coding agents**: Claude Code, Codex, Cursor, Gemini CLI
3. **Automatic updates** where the agent supports it (Claude Code)
4. **Single-command updates** for everything else: `uv tool upgrade lithosai-motus`
5. **Plugin version = CLI version** (kept in sync manually)
6. **Agent-driven upgrades**: when the CLI prints an update-available message, the coding agent runs the upgrade command automatically

## Design

### Source of truth

Plugin files live at `src/motus/plugins/motus/` inside the Python package. They are bundled as `package-data` and installed to site-packages by `uv tool install`.

### Repo layout

```
src/motus/plugins/                    <-- package data
    motus/                            <-- the actual plugin
        .claude-plugin/plugin.json
        .codex-plugin/plugin.json
        .cursor-plugin/plugin.json
        skills/motus/
            SKILL.md
            REFERENCE.md, PATTERNS.md, EXAMPLES.md, ...
            gemini-extension.json     <-- Gemini manifest listing all context files

plugins/motus                         <-- symlink -> ../src/motus/plugins/motus

.agents/plugins/marketplace.json      <-- Codex marketplace (source: "./.agents/plugins/motus")
.agents/plugins/motus                 <-- symlink -> ../../src/motus/plugins/motus
.claude-plugin/marketplace.json       <-- Claude Code marketplace (source: "./plugins/motus")
```

All marketplace files use `"name": "LithosAI"` so that local and GitHub-based registrations overwrite rather than duplicate each other.

### Per-agent deployment (`install.sh`)

| Agent | Deployment method | Installed location |
|-------|-------------------|--------------------|
| Claude Code | `claude plugin marketplace add` from GitHub | `~/.claude/plugins/` (managed by Claude Code, auto-updates) |
| Codex | Symlink skill directory | `~/.codex/skills/motus` → package skill path |
| Cursor | Symlink skill directory | `~/.cursor/skills/motus` → package skill path |
| Gemini | Symlink skill directory as extension | `~/.gemini/extensions/motus` → package skill path |

Claude Code gets its own managed copy via the GitHub marketplace with auto-update enabled. The other three agents get symlinks to the skill directory inside the uv-managed package. Full plugin installs (marketplace or plugin directory) are not used for Codex, Cursor, or Gemini because a plugin containing a skill with the same name causes duplicate registration.

Gemini CLI uses `gemini-extension.json` to discover context files (it does not read `SKILL.md` by default). The manifest lists all markdown files in the skill directory.

The repo-root marketplace files and plugin manifests (`.codex-plugin/`, `.cursor-plugin/`) remain for GitHub-based discovery when agents browse the repo directly.

### Update matrix

| Component | Update mechanism | Frequency |
|-----------|------------------|-----------|
| CLI | `uv tool upgrade lithosai-motus` | Manual (prompted by version check) |
| Claude Code plugin | Auto-update from GitHub | Automatic |
| Codex/Cursor/Gemini skill | `uv tool upgrade` (symlinks, same paths) | With CLI upgrade |

The CLI checks PyPI once every 24 hours and prints a message to stderr when a new version is available. SKILL.md instructs the coding agent to run the upgrade command when it sees this message, so updates happen organically during coding sessions.

### Version bumping

When releasing a new version, update these files:

1. `pyproject.toml` (`version = "X.Y.Z"`)
2. `src/motus/plugins/motus/.claude-plugin/plugin.json` (`"version": "X.Y.Z"`)
3. `src/motus/plugins/motus/.codex-plugin/plugin.json` (`"version": "X.Y.Z"`)
4. `src/motus/plugins/motus/.cursor-plugin/plugin.json` (`"version": "X.Y.Z"`)
5. `src/motus/plugins/motus/skills/motus/gemini-extension.json` (`"version": "X.Y.Z"`)
6. `.claude-plugin/marketplace.json` (`metadata.version` — marketplace version, independent of plugin)
7. `.cursor-plugin/marketplace.json` (`metadata.version` — marketplace version, independent of plugin)
