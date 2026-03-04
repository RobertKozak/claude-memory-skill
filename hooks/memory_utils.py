#!/usr/bin/env python3.13
"""
Shared utilities for claude-memory hooks.

Imported by session-start.py, session-end.py, and pre-compact.py.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


MEMORY_DIR = Path.home() / ".claude" / "memory"


# ── Project identity ───────────────────────────────────────────────────────────

def get_project_name(cwd: str = None) -> str:
    """Get project name from git root if available, else current directory basename."""
    base = cwd or os.getcwd()
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, cwd=base,
        )
        if result.returncode == 0:
            return os.path.basename(result.stdout.strip())
    except Exception:
        pass
    return os.path.basename(base)


def read_file_safe(path: Path) -> str | None:
    """Read a file, returning None if it doesn't exist or is empty."""
    try:
        if path.exists() and path.stat().st_size > 0:
            return path.read_text().strip()
    except Exception:
        pass
    return None


# ── Transcript parsing ─────────────────────────────────────────────────────────

_NOISE_MESSAGES = {"wakeup", "hello", "hi", "hey"}
_SKIP_PREFIXES = ("Summarize this Claude Code session",)


def extract_user_messages(transcript_path: str, max_messages: int = 5) -> list[str]:
    """Extract recent user messages from the transcript."""
    try:
        path = Path(transcript_path).expanduser()
        if not path.exists():
            return []

        lines = path.read_text().splitlines()
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

                if isinstance(content, str):
                    text = content.strip()
                    if (text and not text.startswith("<") and not text.startswith("[")
                            and text.lower() not in _NOISE_MESSAGES
                            and not any(text.startswith(p) for p in _SKIP_PREFIXES)):
                        user_messages.append(text)

                elif isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            text = block.get("text", "").strip()
                            if (text and not text.startswith("<") and not text.startswith("[")
                                    and text.lower() not in _NOISE_MESSAGES
                                    and not any(text.startswith(p) for p in _SKIP_PREFIXES)):
                                user_messages.append(text)
                                break

            except json.JSONDecodeError:
                continue

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
    """Extract tools used and last assistant response from transcript."""
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
    """Try to infer what should happen next from the last assistant response."""
    keywords = ["next", "will", "going to", "let me", "todo", "remaining", "still need"]
    for line in last_response.split("\n"):
        lower = line.lower().strip()
        if any(kw in lower for kw in keywords):
            return line.strip()[:200]
    return ""


def extract_conversation(transcript_path: str, max_chars: int = 10000) -> str:
    """Build a readable conversation string from the full transcript."""
    try:
        path = Path(transcript_path).expanduser()
        if not path.exists():
            return ""

        turns = []
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                msg_type = obj.get("type")
                content = obj.get("message", {}).get("content", "")

                if msg_type == "user":
                    text = ""
                    if isinstance(content, str):
                        text = content.strip()
                    elif isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                text = block.get("text", "").strip()
                                break
                    if text and not text.startswith("<") and not text.startswith("[") and text.lower() not in _NOISE_MESSAGES:
                        turns.append(f"User: {text[:400]}")

                elif msg_type == "assistant" and isinstance(content, list):
                    tools, response_text = [], ""
                    for block in content:
                        if not isinstance(block, dict):
                            continue
                        if block.get("type") == "tool_use":
                            tools.append(block.get("name", ""))
                        elif block.get("type") == "text":
                            response_text = block.get("text", "").strip()
                    parts = []
                    if response_text:
                        parts.append(response_text[:400])
                    if tools:
                        parts.append(f"[tools: {', '.join(tools)}]")
                    if parts:
                        turns.append(f"Assistant: {' '.join(parts)}")

            except json.JSONDecodeError:
                continue

        conversation = "\n".join(turns)
        if len(conversation) > max_chars:
            conversation = "...[earlier conversation trimmed]...\n" + conversation[-max_chars:]
        return conversation

    except Exception:
        return ""


# ── AI summarization ───────────────────────────────────────────────────────────

def summarize_with_claude(transcript_path: str) -> dict | None:
    """Use claude CLI to generate a session summary. Returns None on failure."""
    conversation = extract_conversation(transcript_path)
    if not conversation:
        return None

    try:
        prompt = (
            "Summarize this Claude Code session. Return exactly these two sections:\n\n"
            "## What was worked on\n"
            "(bullet points — what was discussed, requested, and implemented/completed)\n\n"
            "## Next up\n"
            "(one line — what should happen next, or leave blank if nothing was mentioned)\n\n"
            "Be concise. Focus on outcomes, not step-by-step details.\n\n"
            f"Session transcript:\n{conversation}"
        )
        result = subprocess.run(
            ["claude", "-p", "--no-session-persistence", prompt],
            capture_output=True,
            text=True,
            timeout=60,
            stdin=subprocess.DEVNULL,
            env={**os.environ, "CLAUDE_MEMORY_SKIP": "1"},
        )
        if result.returncode != 0:
            return None

        text = result.stdout.strip()
        items, next_up, in_section = [], "", None

        for line in text.splitlines():
            stripped = line.strip()
            if stripped == "## What was worked on":
                in_section = "worked_on"
            elif stripped == "## Next up":
                in_section = "next_up"
            elif stripped.startswith("## "):
                in_section = None
            elif in_section == "worked_on" and stripped.startswith("- "):
                items.append(stripped)
            elif in_section == "next_up" and stripped:
                next_up = stripped.lstrip("- ")
                in_section = None

        return {"items": items, "next_up": next_up}

    except Exception:
        return None


def build_summary(session_data: dict) -> str:
    """Build a session summary, using Claude API when available."""
    transcript = session_data.get("transcript_path", "")
    parts = [
        f"Session ID: {session_data.get('session_id', 'unknown')}",
        f"Session ended: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
    ]

    if not transcript:
        return "\n".join(parts)

    info = extract_tools_and_completions(transcript)
    tool_summary = ", ".join(info["tools"][:10]) if info["tools"] else ""

    ai = summarize_with_claude(transcript)
    if ai:
        if ai["items"]:
            parts.append("\n## What was worked on")
            parts.extend(ai["items"])
        if tool_summary:
            parts.append(f"\n## Tools used\n{tool_summary}")
        if ai["next_up"]:
            parts.append(f"\n## Next up\n{ai['next_up']}")
    else:
        user_msgs = extract_user_messages(transcript)
        if user_msgs:
            parts.append("\n## What was worked on")
            for msg in user_msgs[-5:]:
                parts.append(f"- {msg}")
        if tool_summary:
            parts.append(f"\n## Tools used\n{tool_summary}")
        next_action = infer_next_action(info["last_response"])
        if next_action:
            parts.append(f"\n## Next up\n{next_action}")

    return "\n".join(parts)


# ── Project session file ────────────────────────────────────────────────────────

def append_session_entry(project: str, summary: str, session_id: str) -> None:
    """Append or replace a session entry in the project memory file."""
    project_file = MEMORY_DIR / "projects" / f"{project}.md"
    new_section = f"\n## {session_id} — {project}\n\n{summary}\n"

    if not project_file.exists():
        project_file.write_text(f"# {project}\n\n---\n{new_section}")
        return

    content = project_file.read_text()
    parts = content.split("\n---\n")
    header = f"\n## {session_id} — "

    for i, part in enumerate(parts):
        if part.startswith(header):
            parts[i] = new_section
            project_file.write_text("\n---\n".join(parts))
            return

    project_file.write_text(content + f"\n---\n{new_section}")


def get_last_session_notes(project: str) -> str | None:
    """Return the most recent session entry for this project."""
    project_file = MEMORY_DIR / "projects" / f"{project}.md"
    try:
        if not project_file.exists():
            return None
        content = project_file.read_text()
        parts = content.split("\n---\n")
        matching = [p.strip() for p in parts if f"— {project}" in p]
        return matching[-1] if matching else None
    except Exception:
        return None
