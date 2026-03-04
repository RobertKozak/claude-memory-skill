---
name: memory-info
description: Show memory system status and storage details. Use when the user wants to see how much is stored.
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

Use the Bash tool with `ls -lh` to get file sizes. Use the Read tool to read file contents.

For token counts, use `uv run python3` with tiktoken:

```python
import os, tiktoken
enc = tiktoken.encoding_for_model('gpt-4')
files = ['~/.claude/memory/profile.md', '~/.claude/memory/SESSION_NOTES.md', ...]
for f in files:
    path = os.path.expanduser(f)
    if os.path.exists(path):
        tokens = len(enc.encode(open(path).read()))
        print(f'{tokens} tokens  {os.path.basename(f)}')
```

If tiktoken is not available, fall back to the ~4 chars/token heuristic and note it's estimated.

Include a token count column in the Project Memories table and show total tokens at the bottom.

If the memory directory doesn't exist at all, inform the user that the plugin is installed but no memories have been saved yet. Suggest using `/remember` to get started.
