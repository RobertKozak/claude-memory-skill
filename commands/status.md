---
name: status
description: Show memory system status and storage details
---

Show the current state of the Claude Memory system.

## Instructions

1. Check if `~/.claude/memory/` directory exists
2. Read `~/.claude/memory/profile.md` — show if it exists and its size
3. List all files in `~/.claude/memory/projects/` — show each project name and file size
4. Read `~/.claude/memory/.last-session` — show when the last session was

### Output format

Present a clean status overview:

```
## Claude Memory Status

**Memory location:** ~/.claude/memory/

### Profile
[file size or "not created yet"]
[number of sections/topics if exists]

### Project Memories
[list each .md file in projects/ with name and size]
[or "No project memories yet"]

### Last Session
[timestamp and how long ago]
```

Use the Bash tool with `ls -lh` and `wc -l` to get file sizes and line counts. Use the Read tool to read file contents.

If the memory directory doesn't exist at all, inform the user that the plugin is installed but no memories have been saved yet. Suggest using `/remember` to get started.
