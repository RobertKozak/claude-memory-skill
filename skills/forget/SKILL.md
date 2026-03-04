---
name: forget
description: Remove something from Claude's persistent memory. Use when the user says "forget X", "stop remembering Y", "remove that from memory", or "delete that preference".
---

The user wants to remove something from memory: **$ARGUMENTS**

## Instructions

1. Read both memory files:
   - `~/.claude/memory/profile.md` (global preferences)
   - `~/.claude/memory/projects/{project_name}.md` (project-specific, where `{project_name}` is the current directory name)

2. Search both files for content matching what the user wants to forget. Look for:
   - An exact bullet point or line
   - A whole section (if the user names a topic or header)
   - A partial match if the full text is unclear

3. If a match is found:
   - Use the Edit tool to remove the matching line(s) or section
   - If removing a section leaves the file with only empty headers, clean those up too
   - Confirm what was removed and from which file

4. If no match is found in either file:
   - Tell the user the content wasn't found
   - Optionally show what IS currently saved so they can identify the right phrasing

5. If the arguments are vague (e.g. "forget everything about X"), remove all lines/sections related to that topic.

### Notes
- Never delete the entire file — only remove the specific content requested
- If removing a bullet point from a list, remove only that line
- If removing a whole `##` section, remove the header and all its body lines
