#!/usr/bin/env python3.13
"""
SessionStart hook — Reads memory files and injects them into context.

This is the magic: when Claude starts a session, it automatically knows
your preferences and what you were working on last time.
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
    read_file_safe,
    get_last_session_notes,
)


def get_user_name() -> str | None:
    """Extract user name from profile.md, if saved."""
    try:
        profile = (MEMORY_DIR / "profile.md").read_text()
        for line in profile.splitlines():
            if "name:" in line.lower():
                parts = line.split(":", 1)
                if len(parts) == 2:
                    name = parts[1].strip()
                    if name:
                        return name
    except Exception:
        pass
    return None


def format_time_since(timestamp_str: str) -> str:
    """Format how long ago the last session was."""
    try:
        last = datetime.fromisoformat(timestamp_str)
        now = datetime.now()
        delta = now - last
        minutes = int(delta.total_seconds() / 60)

        if minutes < 2:
            return "just now"
        elif minutes < 60:
            return f"{minutes} minutes ago"
        elif minutes < 120:
            return "about an hour ago"
        elif minutes < 1440:
            return f"{minutes // 60} hours ago"
        elif minutes < 2880:
            return "yesterday"
        elif minutes < 10080:
            return f"{minutes // 1440} days ago"
        elif minutes < 20160:
            return "about a week ago"
        elif minutes < 43200:
            return f"{minutes // 10080} weeks ago"
        else:
            return f"{minutes // 43200} months ago"
    except Exception:
        return "some time ago"


def build_context(cwd: str = None) -> str:
    """Build the context injection from memory files."""
    project = get_project_name(cwd)
    parts = []

    # --- User Profile ---
    profile = read_file_safe(MEMORY_DIR / "profile.md")
    if profile:
        parts.append(f"## Your Preferences\n\n{profile}")

    # --- Last Session Notes (most recent entry for this project) ---
    last_notes = get_last_session_notes(project)
    if last_notes:
        parts.append(f"## Last Session Notes\n\n{last_notes}")

    # --- Time Context ---
    last_session_str = read_file_safe(MEMORY_DIR / ".last-session")
    if last_session_str:
        time_ago = format_time_since(last_session_str)
        try:
            last_dt = datetime.fromisoformat(last_session_str)
            last_fmt = last_dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            last_fmt = last_session_str.strip()
        parts.append(f"## Session Context\n\nLast session was **{time_ago}** ({last_fmt}).")

    # --- Startup Prompt ---
    startup_prompt = read_file_safe(MEMORY_DIR / "startup-prompt.md")
    if startup_prompt:
        parts.append(f"## Startup Prompt\n\n{startup_prompt}")

    if not parts:
        return ""

    # Build greeting directive
    name = get_user_name()
    greeting_name = f" {name}" if name else ""
    greeting_directive = (
        f"Greet the user as '{greeting_name.strip() or 'there'}' by name on session start. "
        if name else
        "Greet the user warmly on session start. "
    )

    header = (
        "**Claude Memory — Context from previous sessions.**\n"
        "The information below was saved from past sessions. "
        "Use it to provide continuity — remember preferences, "
        "pick up where you left off, and avoid re-asking things the user already told you.\n"
        f"{greeting_directive}"
        "Reference the last thing worked on from the project memory. "
        "If there is a 'Next up' section, offer it as a suggestion for what to continue. "
        "Keep the greeting brief and natural.\n"
        "Memory is stored in `~/.claude/memory/`. "
        "The user can run `/remember`, `/recall`, or `/memory-info` to manage it.\n"
    )

    return header + "\n\n" + "\n\n---\n\n".join(parts)


def read_session_data() -> dict:
    """Read session data from stdin (provided by Claude Code)."""
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        return {
            "session_id": data.get("session_id", "unknown"),
            "cwd": data.get("cwd") or os.getcwd(),
        }
    except Exception:
        return {"session_id": "unknown", "cwd": os.getcwd()}


def main():
    """Main entry point."""
    try:
        session_data = read_session_data()
        cwd = session_data.get("cwd")

        # Ensure memory directory exists
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        (MEMORY_DIR / "projects").mkdir(exist_ok=True)

        # Build context
        context = build_context(cwd)

        if context:
            full_context = f"<system-reminder>\n{context}\n</system-reminder>"
        else:
            full_context = (
                "<system-reminder>\n"
                "Claude Memory plugin is active but no memories saved yet. "
                "The user can use `/remember` to save preferences or project context.\n"
                "</system-reminder>"
            )

        result = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": full_context,
            }
        }

        sys.stdout.buffer.write(json.dumps(result).encode("utf-8"))
        sys.stdout.buffer.write(b"\n")
        sys.stdout.buffer.flush()
        return 0

    except Exception as e:
        sys.stderr.write(f"claude-memory session-start: {e}\n")
        return 0


if __name__ == "__main__":
    sys.exit(main())
