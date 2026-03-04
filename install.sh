#!/bin/bash
#
# claude-memory installer
#
# 1. Creates the memory directory structure
# 2. Registers hooks directly in ~/.claude/settings.json
# 3. Symlinks skills into ~/.claude/skills/
#
# No /plugin install needed — this wires everything up directly.
#

set -e

MEMORY_DIR="$HOME/.claude/memory"
PLUGIN_DIR="$(cd "$(dirname "$0")" && pwd)"
SETTINGS_FILE="$HOME/.claude/settings.json"
SKILLS_DIR="$HOME/.claude/skills"

echo "=== claude-memory installer ==="
echo ""

# ── 1. Memory directory ──────────────────────────────────────────────────────
mkdir -p "$MEMORY_DIR/projects"
echo "✓ Memory directory: $MEMORY_DIR"

# Create startup-prompt.md if it doesn't exist
STARTUP_PROMPT="$MEMORY_DIR/startup-prompt.md"
if [ ! -f "$STARTUP_PROMPT" ]; then
    cat > "$STARTUP_PROMPT" <<'EOF'
# Startup Prompt

Instructions here are injected into every Claude session at startup.
Add standing behavioral preferences, reminders, or project-wide rules.

Examples:
- "Always respond concisely and avoid unnecessary preamble."
- "Prefer TypeScript over JavaScript."
- "Never commit without asking first."
EOF
    echo "✓ Created startup prompt: $STARTUP_PROMPT"
else
    echo "✓ Startup prompt already exists: $STARTUP_PROMPT"
fi

# ── 2. Python dependencies ────────────────────────────────────────────────────
echo "✓ Checking Python dependencies"
if ! python3.13 -c "import anthropic" 2>/dev/null; then
    echo "  Installing anthropic package for python3.13..."
    if command -v uv &>/dev/null; then
        uv pip install --quiet --python python3.13 anthropic
    else
        python3.13 -m pip install --quiet --break-system-packages anthropic
    fi
    echo "  ✓ anthropic installed"
else
    echo "  ✓ anthropic already installed"
fi

# ── 3. Register hooks in settings.json ───────────────────────────────────────
echo "✓ Registering hooks in $SETTINGS_FILE"

python3 - "$PLUGIN_DIR" "$SETTINGS_FILE" <<'PYEOF'
import json, os, sys

plugin_dir = sys.argv[1]
settings_file = sys.argv[2]

# Load existing settings or start fresh
if os.path.exists(settings_file):
    with open(settings_file, "r") as f:
        settings = json.load(f)
else:
    settings = {}

# Build hook entries using absolute paths
hooks = settings.setdefault("hooks", {})

def set_hook(hooks, event, script_name):
    script_path = os.path.join(plugin_dir, "hooks", script_name)
    entry = {
        "hooks": [
            {
                "type": "command",
                "command": script_path
            }
        ]
    }
    # Replace any existing claude-memory hook entry, or add new
    existing = hooks.get(event, [])
    # Remove old entries from this plugin
    existing = [e for e in existing if not any(
        plugin_dir in h.get("command", "") for h in e.get("hooks", [])
    )]
    existing.append(entry)
    hooks[event] = existing

set_hook(hooks, "SessionStart", "session-start.py")
set_hook(hooks, "SessionEnd", "session-end.py")
set_hook(hooks, "PreCompact", "pre-compact.py")

# Grant read/write permissions for memory files so Claude doesn't prompt
memory_patterns = [
    "Read(~/.claude/memory/**)",
    "Write(~/.claude/memory/**)",
    "Edit(~/.claude/memory/**)",
]
permissions = settings.setdefault("permissions", {})
allowed = permissions.setdefault("allow", [])
# Remove stale absolute-path entries from older installs
expanded_dir = os.path.expanduser("~/.claude/memory")
allowed[:] = [p for p in allowed if not (
    p.startswith(f"Read({expanded_dir}") or
    p.startswith(f"Write({expanded_dir}") or
    p.startswith(f"Edit({expanded_dir}")
)]
for pattern in memory_patterns:
    if pattern not in allowed:
        allowed.append(pattern)

# Remove old extraKnownMarketplaces entry if it's only for this plugin
marketplaces = settings.get("extraKnownMarketplaces", {})
if "local" in marketplaces:
    local_path = marketplaces["local"].get("source", {}).get("path", "")
    parent = os.path.dirname(plugin_dir)
    if local_path == parent:
        del marketplaces["local"]
        if not marketplaces:
            del settings["extraKnownMarketplaces"]
        else:
            settings["extraKnownMarketplaces"] = marketplaces

with open(settings_file, "w") as f:
    json.dump(settings, f, indent=2)
    f.write("\n")

print(f"  SessionStart  -> hooks/session-start.py")
print(f"  SessionEnd    -> hooks/session-end.py")
print(f"  PreCompact    -> hooks/pre-compact.py")
print(f"  Permissions   -> Read/Write/Edit on {expanded_dir}/**")
PYEOF

# ── 4. Symlink skills ─────────────────────────────────────────────────────────
echo "✓ Linking skills into $SKILLS_DIR"

mkdir -p "$SKILLS_DIR"

for skill in remember recall memory-info compact-notes forget; do
    src="$PLUGIN_DIR/skills/$skill"
    dst="$SKILLS_DIR/$skill"
    if [ -L "$dst" ]; then
        rm "$dst"
    elif [ -d "$dst" ]; then
        echo "  ! $dst exists and is not a symlink — skipping"
        continue
    fi
    ln -s "$src" "$dst"
    echo "  /claude-memory:$skill -> $dst"
done

# ── 5. Done ───────────────────────────────────────────────────────────────────
echo ""
echo "=== Install complete ==="
echo ""
echo "  Skills available (no restart needed):"
echo "    /remember <thing>   — Save a preference or project note"
echo "    /recall [query]     — Show what Claude remembers"
echo "    /memory-info        — Show memory system status"
echo "    /compact-notes      — Summarize old session notes to save space"
echo "    /forget <thing>     — Remove something from memory"
echo ""
echo "  Hooks registered (active on next Claude session):"
echo "    SessionStart  — Injects saved memory into context"
echo "    SessionEnd    — Auto-saves what you worked on"
echo "    PreCompact    — Preserves memory through context compression"
echo ""
echo "  Memory stored in: $MEMORY_DIR/
  Startup prompt:   $MEMORY_DIR/startup-prompt.md"
echo ""
