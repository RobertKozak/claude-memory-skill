#!/usr/bin/env python3
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


MEMORY_DIR = Path.home() / ".claude" / "memory"


def get_project_name() -> str:
    """Get project name from current working directory."""
    return os.path.basename(os.getcwd())


def get_user_name() -> str | None:
    """Extract user name from profile.md, if saved."""
    try:
        profile = (MEMORY_DIR / "profile.md").read_text()
        for line in profile.splitlines():
            if "name:" in line.lower():
                # e.g. "- Name: Robert" or "Name: Robert"
                parts = line.split(":", 1)
                if len(parts) == 2:
                    name = parts[1].strip()
                    if name:
                        return name
    except Exception:
        pass
    return None


def read_file_safe(path: Path) -> str | None:
    """Read a file, returning None if it doesn't exist or is empty."""
    try:
        if path.exists() and path.stat().st_size > 0:
            return path.read_text().strip()
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


def build_context() -> str:
    """Build the context injection from memory files."""
    project = get_project_name()
    parts = []

    # --- User Profile ---
    profile = read_file_safe(MEMORY_DIR / "profile.md")
    if profile:
        parts.append(f"## Your Preferences\n\n{profile}")

    # --- Project Memory ---
    project_memory = read_file_safe(MEMORY_DIR / "projects" / f"{project}.md")
    if project_memory:
        parts.append(f"## Project: {project}\n\n{project_memory}")

    # --- Time Context ---
    last_session_str = read_file_safe(MEMORY_DIR / ".last-session")
    if last_session_str:
        time_ago = format_time_since(last_session_str)
        parts.append(f"## Session Context\n\nLast session was **{time_ago}**.")

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

    # Wrap everything in instructions
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
        "The user can run `/remember`, `/recall`, or `/status` to manage it.\n"
    )

    return header + "\n\n" + "\n\n---\n\n".join(parts)


def main():
    """Main entry point."""
    try:
        # Read session data from stdin (provided by Claude Code)
        try:
            json.loads(sys.stdin.buffer.read().decode("utf-8"))
        except Exception:
            pass

        # Ensure memory directory exists
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        (MEMORY_DIR / "projects").mkdir(exist_ok=True)

        # Initialize project memory file if this is the first session
        project = get_project_name()
        project_file = MEMORY_DIR / "projects" / f"{project}.md"
        if not project_file.exists():
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            name = get_user_name() or "Unknown"
            project_file.write_text(
                f"## Project\n{project}\n\n"
                f"## User\n{name}\n\n"
                f"## Session\n{now}\n"
            )

        # Build context
        context = build_context()

        if context:
            full_context = f"<system-reminder>\n{context}\n</system-reminder>"
        else:
            full_context = (
                "<system-reminder>\n"
                "Claude Memory plugin is active but no memories saved yet. "
                "The user can use `/remember` to save preferences or project context.\n"
                "</system-reminder>"
            )

        # Output for Claude Code
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
        # Never crash — just skip injection
        sys.stderr.write(f"claude-memory session-start: {e}\n")
        return 0


if __name__ == "__main__":
    sys.exit(main())
