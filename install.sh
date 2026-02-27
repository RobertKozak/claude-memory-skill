#!/bin/bash
#
# claude-memory installer
#
# Creates the memory directory and shows how to load the plugin.
#

set -e

MEMORY_DIR="$HOME/.claude/memory"
PLUGIN_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== claude-memory installer ==="
echo ""

# Create memory directory structure
mkdir -p "$MEMORY_DIR/projects"
echo "Created $MEMORY_DIR/"
echo "Created $MEMORY_DIR/projects/"

echo ""
echo "=== How to use ==="
echo ""
echo "Option 1 — Load for a single session (dev/testing):"
echo ""
echo "  claude --plugin-dir $PLUGIN_DIR"
echo ""
echo "Option 2 — Always load via shell alias:"
echo ""
echo "  echo 'alias claude=\"claude --plugin-dir $PLUGIN_DIR\"' >> ~/.zshrc"
echo "  source ~/.zshrc"
echo ""
echo "Option 3 — Install from within Claude Code:"
echo ""
echo "  /plugin                          # Opens plugin manager"
echo "  /plugin install claude-memory    # If published to a marketplace"
echo ""
echo "=== Skills available ==="
echo ""
echo "  /claude-memory:remember <thing>  — Save a preference or project note"
echo "  /claude-memory:recall [query]    — Show what Claude remembers"
echo "  /claude-memory:status            — Show memory system status"
echo ""
echo "=== Hooks (automatic) ==="
echo ""
echo "  SessionStart  — Injects saved memory into context"
echo "  SessionEnd    — Auto-saves what you worked on"
echo "  PreCompact    — Preserves memory through context compression"
echo ""
echo "Memory is stored in: $MEMORY_DIR/"
echo ""
