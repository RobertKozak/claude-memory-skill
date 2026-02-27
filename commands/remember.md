---
name: remember
description: Save something to Claude's persistent memory
args:
  - what
---

The user wants to save something to persistent memory: **{{what}}**

## Instructions

Determine whether this is a **user preference** (global) or **project-specific** information:

- **User preferences** (tools, workflow, communication style, personal info) → save to `~/.claude/memory/profile.md`
- **Project-specific** (architecture decisions, patterns, conventions, context about this codebase) → save to `~/.claude/memory/projects/{project_name}.md` where `{project_name}` is the current directory name

### Steps

1. Read the target file (if it exists) to see what's already saved
2. Incorporate the new information — don't duplicate, update if the topic already exists
3. Write the updated file back
4. Confirm what was saved and where

### Format Guidelines

Keep the markdown clean and scannable:
- Use `##` headers to organize by topic
- Use bullet points for lists of preferences
- Keep entries concise — these are notes for future sessions, not documentation
- If updating an existing entry, replace it rather than appending a duplicate

### Example profile.md structure
```markdown
## Tools & Workflow
- Always use bun instead of npm
- Prefer TypeScript over JavaScript
- Use Vitest for testing

## Communication
- Be concise, skip unnecessary explanations
- Don't add emojis unless asked

## Environment
- macOS, VS Code, iTerm2
```

### Example project memory structure
```markdown
## Architecture
- Monorepo with apps/ and packages/
- API uses Express + Prisma

## Conventions
- Components in PascalCase
- API routes use kebab-case
- Tests co-located with source files

## Key Decisions
- Chose PostgreSQL over MongoDB for relational data
- Auth uses JWT with refresh tokens
```
