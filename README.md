# claude-memory-skill

A simple (very simple) memory system for claude. Maybe better just use Claude Code Auto memory:[Auto memory](https://code.claude.com/docs/en/memory#auto-memory)

Persistent memory for [Claude Code](https://claude.ai/code) across sessions. Saves what you were working on, your preferences, and project context — and automatically restores it when you start a new session.

## How it works

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

Three hooks run automatically:

- **SessionStart** — reads memory files and injects them into Claude's context so it knows your name, preferences, and what you worked on last time
- **SessionEnd** — writes an AI-summarized session entry to `projects/{name}.md`
- **PreCompact** — re-injects memory before context compression so nothing is lost in long sessions

Memory is stored as plain markdown files in `~/.claude/memory/`.

## Install

```bash
git clone https://github.com/robertkozak/claude-memory-skill
cd claude-memory-skill
./install.sh
```

The installer:

1. Creates `~/.claude/memory/` and `~/.claude/memory/projects/`
2. Registers the three hooks in `~/.claude/settings.json`
3. Symlinks the skills into `~/.claude/skills/`

Requires Python 3.13. No external dependencies.

## Skills

| Skill               | When to use                                                  |
| ------------------- | ------------------------------------------------------------ |
| `/remember <thing>` | Save a preference, decision, or project note                 |
| `/recall [query]`   | Show everything Claude remembers about you                   |
| `/memory-info`      | Show file sizes and token counts for all memory files        |
| `/compact-notes`    | Summarize old session entries to keep the project file small |
| `/forget <thing>`   | Remove something from memory                                 |

## Memory files

```
~/.claude/memory/
├── profile.md              # Global preferences (tools, workflow, style)
├── startup-prompt.md       # Custom instructions injected on session start
├── .last-session           # ISO timestamp of last session end
└── projects/
    ├── my-project.md       # Per-project session history
    └── another-project.md
```

Each project file contains session entries written at the end of every session:

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

## Example

On session start, Claude greets you by name and picks up where you left off:

> Hey Robert! Last session we were adding the `/compact-notes` skill and renaming `/status` to `/memory-info`. Want to pick up where we left off?

Use `/remember` to teach Claude things that should persist:

```
/remember always use uv instead of pip
/remember prefer short, concise responses
/remember this project uses PostgreSQL with Prisma
```
