#!/usr/bin/env python3.13
"""
PreCompact hook — Saves a session snapshot and re-injects memory before context compression.

When Claude Code compacts the conversation (approaching context limit), this hook:
1. Saves the current session state to project memory (snapshot)
2. Re-injects all memory so it survives compaction

Without this, Claude would lose all context injected at session start.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from memory_utils import (
    MEMORY_DIR,
    get_project_name,
    read_file_safe,
    build_summary,
    append_session_entry,
    get_last_session_notes,
)


def read_session_data() -> dict:
    """Read session data from stdin (provided by Claude Code)."""
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        return {
            "session_id": data.get("session_id", "unknown"),
            "transcript_path": data.get("transcript_path", ""),
            "cwd": data.get("cwd") or os.getcwd(),
        }
    except Exception:
        return {
            "session_id": "unknown",
            "transcript_path": "",
            "cwd": os.getcwd(),
        }


def save_session_snapshot(session_data: dict) -> None:
    """Save current session state to project memory file."""
    try:
        project = get_project_name(session_data.get("cwd"))
        summary = build_summary(session_data)

        if len(summary) > 50:
            append_session_entry(project, summary, session_data.get("session_id", "unknown"))

    except Exception as e:
        sys.stderr.write(f"claude-memory pre-compact snapshot: {e}\n")


def build_memory_injection(cwd: str = None) -> str:
    """Build memory context to preserve through compaction."""
    project = get_project_name(cwd)
    parts = []

    profile = read_file_safe(MEMORY_DIR / "profile.md")
    if profile:
        parts.append(f"## Your Preferences\n\n{profile}")

    last_notes = get_last_session_notes(project)
    if last_notes:
        parts.append(f"## Last Session Notes\n\n{last_notes}")

    if not parts:
        return "Claude Memory plugin active. No saved memories to preserve."

    header = (
        "**Memory preserved through compaction.**\n"
        "The following was saved from previous sessions. Continue using this context.\n"
    )

    return header + "\n\n" + "\n\n---\n\n".join(parts)


def main():
    try:
        session_data = read_session_data()

        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        (MEMORY_DIR / "projects").mkdir(exist_ok=True)

        save_session_snapshot(session_data)

        memory = build_memory_injection(session_data.get("cwd"))

        output = {
            "decision": "continue",
            "user_message": f"<system-reminder>\n{memory}\n</system-reminder>",
        }

        print(json.dumps(output))
        return 0

    except Exception as e:
        sys.stderr.write(f"claude-memory pre-compact: {e}\n")
        print(json.dumps({
            "decision": "continue",
            "user_message": "<system-reminder>Claude Memory plugin active.</system-reminder>",
        }))
        return 1


if __name__ == "__main__":
    sys.exit(main())
