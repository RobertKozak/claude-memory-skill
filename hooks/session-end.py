#!/usr/bin/env python3
"""
SessionEnd hook — Auto-saves what happened in the session.

Parses the transcript to extract:
- What the user asked for
- What was completed
- What's still pending
- A suggested next action

Writes this as a clean markdown summary to the project memory file.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


MEMORY_DIR = Path.home() / ".claude" / "memory"


def get_project_name(cwd: str = None) -> str:
    """Get project name from directory."""
    return os.path.basename(cwd or os.getcwd())


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


def extract_user_messages(transcript_path: str, max_messages: int = 5) -> list[str]:
    """Extract recent user messages from the transcript."""
    try:
        path = Path(transcript_path).expanduser()
        if not path.exists():
            return []

        lines = path.read_text().splitlines()
        # Parse last 200 lines to find user messages
        lines_to_parse = lines[-200:] if len(lines) > 200 else lines

        user_messages = []
        for line in lines_to_parse:
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                if obj.get("type") != "user":
                    continue

                content = obj.get("message", {}).get("content", "")

                # Handle string content
                if isinstance(content, str):
                    text = content.strip()
                    # Skip system messages and hooks
                    if text and not text.startswith("<") and not text.startswith("["):
                        user_messages.append(text)

                # Handle content block arrays
                elif isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            text = block.get("text", "").strip()
                            if text and not text.startswith("<") and not text.startswith("["):
                                user_messages.append(text)
                                break

            except json.JSONDecodeError:
                continue

        # Return the last N unique messages
        seen = set()
        unique = []
        for msg in reversed(user_messages):
            short = msg[:200]
            if short not in seen:
                seen.add(short)
                unique.insert(0, short)
            if len(unique) >= max_messages:
                break

        return unique

    except Exception:
        return []


def extract_tools_and_completions(transcript_path: str) -> dict:
    """Extract completed tasks and tools used from transcript."""
    try:
        path = Path(transcript_path).expanduser()
        if not path.exists():
            return {"tools": [], "last_response": ""}

        lines = path.read_text().splitlines()
        lines_to_parse = lines[-150:] if len(lines) > 150 else lines

        tools_used = set()
        last_response = ""

        for line in lines_to_parse:
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                if obj.get("type") != "assistant":
                    continue

                content = obj.get("message", {}).get("content", [])
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "tool_use":
                        name = block.get("name", "")
                        if name:
                            tools_used.add(name)
                    elif block.get("type") == "text":
                        text = block.get("text", "").strip()
                        if text:
                            last_response = text

            except json.JSONDecodeError:
                continue

        return {
            "tools": sorted(tools_used),
            "last_response": last_response[:500],
        }

    except Exception:
        return {"tools": [], "last_response": ""}


def infer_next_action(last_response: str) -> str:
    """Try to infer what should happen next from the last response."""
    keywords = ["next", "will", "going to", "let me", "todo", "remaining", "still need"]
    for line in last_response.split("\n"):
        lower = line.lower().strip()
        if any(kw in lower for kw in keywords):
            return line.strip()[:200]
    return ""


def build_summary(session_data: dict) -> str:
    """Build a session summary from transcript data."""
    transcript = session_data.get("transcript_path", "")
    parts = [f"Session ended: {datetime.now().strftime('%Y-%m-%d %H:%M')}"]

    if not transcript:
        return "\n".join(parts)

    # User messages
    user_msgs = extract_user_messages(transcript)
    if user_msgs:
        parts.append("\n## What was worked on")
        for msg in user_msgs[-5:]:
            parts.append(f"- {msg}")

    # Tools and last response
    info = extract_tools_and_completions(transcript)

    if info["tools"]:
        # Group tools into readable categories
        tool_summary = ", ".join(info["tools"][:10])
        parts.append(f"\n## Tools used\n{tool_summary}")

    # Next action
    next_action = infer_next_action(info["last_response"])
    if next_action:
        parts.append(f"\n## Next up\n{next_action}")

    return "\n".join(parts)


def main() -> int:
    """Main entry point."""
    try:
        session_data = read_session_data()

        # Ensure memory directory exists
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        (MEMORY_DIR / "projects").mkdir(exist_ok=True)

        # Build session summary
        summary = build_summary(session_data)

        # Only save if we have meaningful content
        if len(summary) > 50:
            project = get_project_name(session_data.get("cwd"))
            project_file = MEMORY_DIR / "projects" / f"{project}.md"
            project_file.write_text(summary)

        # Update last session timestamp
        session_file = MEMORY_DIR / ".last-session"
        session_file.write_text(datetime.now().isoformat())

        return 0

    except Exception as e:
        sys.stderr.write(f"claude-memory session-end: {e}\n")
        return 0  # Never block user exit


if __name__ == "__main__":
    sys.exit(main())
