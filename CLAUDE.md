# Claude Memory Skill

This project is a Claude Code plugin that adds persistent memory across sessions using markdown files and hooks.

## Skills

### `/remember <thing>`
Use when the user says things like:
- "remember this"
- "always do X"
- "never do Y"
- "I prefer..."
- "save that"
- "keep that in mind for next time"

Saves to `~/.claude/memory/profile.md` (global preferences) or `~/.claude/memory/projects/{name}.md` (project-specific), depending on context.

### `/recall [query]`
Use when the user asks:
- "what do you know about me?"
- "what do you remember?"
- "what did we work on last time?"
- "do you remember my preferences?"

Shows everything currently saved in memory, optionally filtered by a search term.

### `/memory-info`
Use when the user asks:
- "how much is stored?"
- "what's in memory?"
- "show me memory status"
- "is the memory plugin working?"

Shows file sizes, project count, and last session timestamp.

## Session Management

Sessions are tracked automatically via hooks — no manual action needed.

**On session start:**
- If no project memory file exists for the current directory, one is created automatically with three sections: `## Project` (directory name), `## User` (name from profile if known), and `## Session` (session ID + datetime)
- Always read `~/.claude/memory/SESSION_NOTES.md` to surface the most recent session entry for this project
- All saved memory is injected into context so Claude is immediately aware of past work
- Always greet the user by name (from `profile.md`) and reference the last thing worked on (from `SESSION_NOTES.md` or project memory)
- If a `## Next up` section exists in project memory, offer it as a suggestion for what to continue
- Keep the greeting brief and natural — one or two sentences

**On session end:**
- A summary of what happened (user messages, tools used, next actions) is always written to `~/.claude/memory/SESSION_NOTES.md` as a new entry keyed by session ID
- The project memory file is also updated with the latest session summary
- `SESSION_NOTES.md` is a running chronological log — entries are appended, never overwritten

`SESSION_NOTES.md` format:
```
# Session Notes

---

## {session_id} — my-project

Session ID: {session_id}
Session ended: 2026-02-27 14:00

## What was worked on
- ...

## Tools used
...
```

## Memory File Locations

- `~/.claude/memory/profile.md` — global user preferences (tools, workflow, communication style)
- `~/.claude/memory/projects/{project-name}.md` — per-project context, keyed by directory name
- `~/.claude/memory/.last-session` — ISO timestamp of the last session end

## Hooks

- **SessionStart** — auto-injects memory into context at the start of every session
- **SessionEnd** — auto-saves a session summary to project memory on exit
- **PreCompact** — re-injects memory before context compression so it is never lost

Do not manually edit hook output files. Use the skills above to manage memory.
