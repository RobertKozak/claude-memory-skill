---
marp: true
theme: default
paginate: true
style: |
  section {
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    background: #0f1117;
    color: #e8e8e8;
    padding-top: 28px;
  }
  h1 {
    color: #d97706;
    font-size: 2.2rem;
    border-bottom: 2px solid #d97706;
    padding-bottom: 0.3rem;
  }
  h2 {
    color: #fbbf24;
    font-size: 1.6rem;
  }
  code {
    background: #1e2130;
    color: #7dd3fc;
    padding: 0.1em 0.4em;
    border-radius: 4px;
  }
  pre {
    background: #1e2130;
    border-left: 4px solid #d97706;
    border-bottom: 2px solid #d97706;
    padding: 0.5rem 1rem;
    font-size: 0.72rem;
    line-height: 1.3;
  }
  pre code {
    background: transparent;
    padding: 0;
  }
  ul li {
    margin-bottom: 0.5rem;
  }
  table {
    width: 100%;
    border-collapse: collapse;
  }
  th {
    background: #1e2130;
    color: #fbbf24;
    padding: 0.5rem 0.8rem;
    border-bottom: 2px solid #d97706;
    text-align: left;
  }
  td {
    background: #161922;
    color: #e8e8e8;
    padding: 0.45rem 0.8rem;
    border-bottom: 1px solid #2a2f3e;
  }
  tr:last-child td {
    border-bottom: 2px solid #d97706;
  }
  .lead {
    font-size: 1.4rem;
    color: #94a3b8;
  }
  section.title {
    display: flex;
    flex-direction: column;
    justify-content: center;
    text-align: center;
  }
  section.title h1 {
    font-size: 3rem;
    border: none;
  }
  section.title p {
    color: #64748b;
    font-size: 1.1rem;
  }
---

<!-- _class: title -->

# Persistent Memory for Claude Code

**A simple file-based setup using hooks and markdown**

Robert Kozak · March 2026

---

# The Problem

Claude Code is powerful — but it forgets **everything** between sessions.

- No memory of your name, preferences, or work style
- No context about what you worked on last time
- You repeat yourself every single session
- You could use 'claude --resume xxxx' but has extra context you might not need

> Every session starts from zero.

---

# The Solution

A lightweight setup that gives Claude **persistent memory** using:

- Plain **markdown files** stored in `~/.claude/memory/`
- **Hooks** that run automatically on session start/end
- **Skills** (slash commands) you invoke when needed

No database. No server. No API calls.
Just files you can read, edit, and version control.

---

# How It Works — Hooks

Three hooks power the memory system automatically:

| Hook           | When it runs               | What it does                         |
| -------------- | -------------------------- | ------------------------------------ |
| `SessionStart` | Every new session          | Reads memory files, injects context  |
| `SessionEnd`   | When you exit Claude       | Writes session summary to disk       |
| `PreCompact`   | Before context compression | Re-injects memory so it's never lost |

**You don't do anything — it just works.**

---

# Memory Files

```
~/.claude/memory/
├── profile.md              # Your name, preferences, work style
├── startup-prompt.md       # Custom instructions for session start
├── .last-session           # Timestamp of last session end
└── projects/
    └── claude-memory-skill.md   # Per-project session history
```

All plain markdown — readable, editable, version-controllable.

---

# What Gets Remembered — Profile

**`profile.md`** — global preferences, persisted across all projects

```markdown
## Personal

- Name: Robert

## Work

- Works on the Seekrflow Everywhere Helm chart

## Upcoming

- Wednesday March 4, 2026 at 11am — presenting to dept engineers
```

---

# What Gets Remembered — Projects

**`projects/{name}.md`** — per-project session history

```markdown
## a1b2c3d4 — my-project

Session ID: a1b2c3d4-...
Session ended: 2026-03-03 15:34

## What was worked on

- Added dark mode support
- Fixed auth bug in login flow

## Next up

- Write tests for the auth fix
```

---

# Skills (Slash Commands)

| Skill               | What it does                               |
| ------------------- | ------------------------------------------ |
| `/remember <thing>` | Save a preference or fact to memory        |
| `/recall`           | Show everything Claude currently remembers |
| `/memory-info`      | Show storage stats and file sizes          |
| `/compact-notes`    | Summarize old session notes to save space  |
| `/forget <thing>`   | Remove something from memory               |

**Example:**

```
/remember always use bun instead of npm
/remember I prefer concise responses, no emojis
```

---

# How It All Connects

```
                ┌──────────────────────────────┐
   reads/writes │       Claude Session         │
   ┌────────────┤  /remember  /recall          │
   │            │  /forget  /compact-notes     │
   │            └─────────────▲────────────────┘
   │                          │ available
   │                 ┌────────┴────────┐
   │                 │    Context      ◄──────────────────┐
   │                 └────────▲────────┘                  │
   │                          │                           │
   │    injects   ┌───────────┴────────┐ re-injects       │ summarize
   │              │                    │                  │
   │   ┌──────────┴─────────┐  ┌───────┴───────┐  ┌───────┴────────┐
   │   │   SessionStart     │  │  PreCompact   │  │  SessionEnd    │
   │   └──────────┬─────────┘  └───────┬───────┘  └───────┬────────┘
   │              │ reads       reads  │          writes  │
   │              │                    │                  │
   │   ┌──────────▼────────────────────▼──────────────────▼────────┐
   │   │                  ~/.claude/memory/                        │
   └──►│          profile.md · projects/{name}.md                  │
       └───────────────────────────────────────────────────────────┘
```

---

# Live Demo

What you'll see:

1. Start a new Claude Code session
2. Claude greets by name and references last session
3. Run `/recall` to inspect what's in memory
4. Run `/remember` to save a new preference
5. End the session — hook writes summary automatically
6. Start a fresh session — Claude picks up seamlessly

---

# Installation

One command:

```bash
curl -fsSL https://raw.githubusercontent.com/robertkozak/claude-memory-skill/main/install.sh | bash
```

What it does:

- Copies hooks to `~/.claude/hooks/`
- Copies skills to `~/.claude/skills/`
- Creates initial memory files
- No dependencies beyond Python 3 (already on your Mac)

**Open source** — fork it, extend it, make it yours.

---

# Key Takeaways

- Claude's context window resets every session — **hooks fix that**
- Memory is just **markdown files** — simple, transparent, portable
- Three hooks + a few skills = **persistent AI assistant**
- Works with any project, not just this one

> The best AI tools are the ones that get out of your way.

---

<!-- _class: title -->

# Questions?

`github.com/robertkozak/claude-memory-skill`

_install.sh · hooks/ · skills/_

---
