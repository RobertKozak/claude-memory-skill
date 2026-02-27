---
name: recall
description: Show what Claude remembers about you and this project. Use when the user asks "what do you know about me" or wants to see saved context.
---

The user wants to see what's in memory. They asked: **$ARGUMENTS**

## Instructions

1. Read `~/.claude/memory/profile.md` (user preferences — global)
2. Read `~/.claude/memory/projects/{project_name}.md` (project-specific memory, where `{project_name}` is the current directory name)
3. Read `~/.claude/memory/.last-session` (last session timestamp)

Present the results clearly:

- If the user asked about something specific, filter and highlight relevant entries
- Otherwise show all saved memory organized by section
- Show when the last session was

### Output format

```
## Profile (global preferences)
[contents of profile.md, or "No preferences saved yet"]

## Project: {name}
[contents of project memory, or "No project memory yet"]

## Last session
[when the last session ended]
```

If both files are empty or missing, let the user know they can use `/remember` to start saving things.
