---
name: compact-notes
description: Compact session notes to save space. Summarizes older entries while keeping recent ones intact. Use when a project memory file grows large or before a presentation.
---

Compact the current project's memory file by summarizing older session entries.

## Instructions

### Step 1 — Identify the current project file

Run `git rev-parse --show-toplevel` (via Bash) to get the git root, then take the basename as the project name.

The project memory file is at `~/.claude/memory/projects/{project-name}.md`.

- If it doesn't exist, tell the user there are no session notes yet.
- Split the content on `\n---\n` to get individual entries. The first part is always the `# {project}` header — skip it. Each remaining part is one session entry.
- If there are **5 or fewer** entries, tell the user the file is already small (show the count) and no compaction is needed.

### Step 2 — Identify what to keep vs. summarize

- **Keep as-is:** the 5 most recent entries (by position, last in the list = most recent)
- **Summarize:** all older entries

Tell the user: "Found N entries — keeping the 5 most recent, summarizing N-5 older ones."

### Step 3 — Summarize the older entries using an agent

Use the **Agent tool** with `subagent_type: "general-purpose"` to summarize the older entries.

Pass this prompt to the agent (substituting the actual content):

```
Summarize these Claude Code session notes into a compact archive.
Focus on what was built, decided, or learned — not the conversation details.

Return exactly this structure:

## Projects worked on
- [project name]: [1-line summary of what was done]
(one line per distinct project)

## Key decisions & patterns
- [bullet point per significant decision, preference, or recurring pattern observed]

## Other notable work
- [anything important that doesn't fit above]

Keep it brief — this is an archive summary, not a full recap.

Session notes to summarize:
{older_entries_content}
```

### Step 4 — Write the compacted file

Build the new project memory file with this structure:

```
# {project-name}

---

## Archived Summary

_(N entries compacted on YYYY-MM-DD)_

{agent summary output}

---

{5 most recent entries, each separated by \n---\n}
```

Write this back to `~/.claude/memory/projects/{project-name}.md`.

### Step 5 — Report results

Show:
- Entries before / after
- Original file size vs new file size (use Bash `wc -c` or `ls -lh`)
- A one-line confirmation of what was archived
