"""Enable auto-update for the LithosAI marketplace in Claude Code.

Usage: python -m motus.configure_plugins
"""

import json
from pathlib import Path

known_path = Path.home() / ".claude" / "plugins" / "known_marketplaces.json"
if known_path.exists():
    known = json.loads(known_path.read_text())
    if "LithosAI" in known:
        known["LithosAI"]["autoUpdate"] = True
        known_path.write_text(json.dumps(known, indent=2) + "\n")
