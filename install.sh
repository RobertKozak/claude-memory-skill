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
echo "=== Installation complete ==="
echo ""
echo "To use the plugin, start Claude Code with:"
echo ""
echo "  claude --plugin-dir $PLUGIN_DIR"
echo ""
echo "Or create an alias in your shell config:"
echo ""
echo "  alias claude='claude --plugin-dir $PLUGIN_DIR'"
echo ""
echo "Commands available:"
echo "  /remember <thing>  — Save a preference or project note"
echo "  /recall [query]    — Show what Claude remembers"
echo "  /status            — Show memory system status"
echo ""
echo "Memory is stored in: $MEMORY_DIR/"
echo ""
