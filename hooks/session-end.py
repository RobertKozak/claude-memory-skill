#!/usr/bin/env python3.13
"""
SessionEnd hook — Auto-saves what happened in the session.

Uses the Claude API to generate a proper AI summary of the session transcript.
Falls back to naive line scanning if the API is unavailable.

Writes a clean markdown summary to the project memory file and SESSION_NOTES.md.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from memory_utils import (
    MEMORY_DIR,
    get_project_name,
    build_summary,
    append_session_entry,
    extract_user_messages,
)


def read_session_data() -> dict:
    """Read session data from stdin (provided by Claude Code)."""
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        return {
            "session_id": data.get("session_id", "unknown"),
            "reason": data.get("reason", "exit"),
            "transcript_path": data.get("transcript_path", ""),
            "cwd": data.get("cwd") or os.getcwd(),
        }
    except Exception:
        return {
            "session_id": "unknown",
            "reason": "exit",
            "transcript_path": "",
            "cwd": os.getcwd(),
        }


def main() -> int:
    if os.environ.get("CLAUDE_MEMORY_SKIP"):
        return 0

    try:
        session_data = read_session_data()

        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        (MEMORY_DIR / "projects").mkdir(exist_ok=True)

        project = get_project_name(session_data.get("cwd"))
        summary = build_summary(session_data)

        transcript = session_data.get("transcript_path", "")
        if not extract_user_messages(transcript):
            return 0

        if len(summary) > 50:
            append_session_entry(project, summary, session_data.get("session_id", "unknown"))

        (MEMORY_DIR / ".last-session").write_text(datetime.now().isoformat())

        return 0

    except Exception as e:
        sys.stderr.write(f"claude-memory session-end: {e}\n")
        return 0  # Never block user exit


if __name__ == "__main__":
    sys.exit(main())
