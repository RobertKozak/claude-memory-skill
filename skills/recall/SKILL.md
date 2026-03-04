---
name: recall
description: Show what Claude remembers about you and this project. Use when the user asks "what do you know about me" or wants to see saved context.
---

The user ran `/recall`. Load memory into context silently.

## Instructions

1. Read `~/.claude/memory/profile.md` (user preferences — global)
2. Read `~/.claude/memory/projects/{project_name}.md` (project-specific memory, where `{project_name}` is the current directory name)
3. Read `~/.claude/memory/.last-session` (last session timestamp)

Do NOT dump the raw file contents to the user. Instead, internalize the information and respond naturally based on the query in `$ARGUMENTS`:

- If `$ARGUMENTS` is empty, briefly acknowledge that memory is loaded and you're ready
- If `$ARGUMENTS` contains a specific question or topic, answer it directly using what you just read
- If files are missing or empty, let the user know there's nothing saved yet and they can use `/remember`
