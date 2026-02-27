#!/usr/bin/env python3
"""
PreCompact hook — Re-injects memory before context compression.

When Claude Code compacts the conversation (approaching context limit),
this hook ensures your profile and project memory survive the compression.
Without this, Claude would lose all the context injected at session start.
"""

import json
import os
import sys
from pathlib import Path


MEMORY_DIR = Path.home() / ".claude" / "memory"


def get_project_name() -> str:
    """Get project name from current working directory."""
    return os.path.basename(os.getcwd())


def read_file_safe(path: Path) -> str | None:
    """Read a file, returning None if it doesn't exist or is empty."""
    try:
        if path.exists() and path.stat().st_size > 0:
            return path.read_text().strip()
    except Exception:
        pass
    return None


def build_memory_injection() -> str:
    """Build memory context to preserve through compaction."""
    project = get_project_name()
    parts = []

    profile = read_file_safe(MEMORY_DIR / "profile.md")
    if profile:
        parts.append(f"## Your Preferences\n\n{profile}")

    project_memory = read_file_safe(MEMORY_DIR / "projects" / f"{project}.md")
    if project_memory:
        parts.append(f"## Project: {project}\n\n{project_memory}")

    if not parts:
        return "Claude Memory plugin active. No saved memories to preserve."

    header = (
        "**Memory preserved through compaction.**\n"
        "The following was saved from previous sessions. Continue using this context.\n"
    )

    return header + "\n\n" + "\n\n---\n\n".join(parts)


def main():
    """Main entry point."""
    try:
        # Read hook input from stdin
        try:
            json.loads(sys.stdin.read())
        except Exception:
            pass

        memory = build_memory_injection()

        output = {
            "decision": "continue",
            "user_message": f"<system-reminder>\n{memory}\n</system-reminder>",
        }

        print(json.dumps(output))
        return 0

    except Exception as e:
        sys.stderr.write(f"claude-memory pre-compact: {e}\n")
        # Fallback — don't break compaction
        print(json.dumps({
            "decision": "continue",
            "user_message": "<system-reminder>Claude Memory plugin active.</system-reminder>",
        }))
        return 1


if __name__ == "__main__":
    sys.exit(main())
