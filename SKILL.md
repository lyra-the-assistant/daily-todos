---
name: daily-todos
description: Daily todo management with native Apple Reminders sync and slash commands. Use when the user wants to manage daily tasks via /todo add, /todo list, /todo complete, /todo delete commands, or set up automated morning digests on macOS.
---

# Daily Todos Skill

Manage daily todos with the macOS Reminders app.

## Use native Reminders automation

- Use `scripts/todo.py` for todo operations.
- The script talks to Apple Reminders through pure AppleScript via `osascript`, not `remindctl` or JXA.
- Keep Apple Reminders as the source of truth for active todo state.
- When a task is completed or removed, sync that change to Reminders instead of only changing local notes.
- Preserve the user's original task language and wording. Do not translate unless explicitly asked.

## Commands

```bash
# Add a todo for today
python3 scripts/todo.py add "任务内容"

# Add with explicit due date
python3 scripts/todo.py add "任务内容" --due 2026-03-31

# List today's todos
python3 scripts/todo.py list

# List all incomplete todos in Daily Todos
python3 scripts/todo.py all

# Complete a todo by short ID
python3 scripts/todo.py complete <id>

# Delete a todo by short ID
python3 scripts/todo.py delete <id>

# Delete all todos in Daily Todos
python3 scripts/todo.py clear

# Morning routine (carry over + defaults)
python3 scripts/todo.py morning

# Show digest
python3 scripts/todo.py digest

# Manage default recurring todos
python3 scripts/todo.py default-add "每日任务"
python3 scripts/todo.py defaults
python3 scripts/todo.py default-remove <index>
```

## Data model

- **Reminders list:** `Daily Todos`
- **Default todos:** `data/defaults.json`
- **Todo metadata:** store the short ID in reminder notes as `[ID: xxx]`

## Output rules

- Present todos in the user's original language.
- Prefer concise, execution-oriented groupings when reorganizing tasks.
- If the user asks to reset from scratch, remove obsolete items from Reminders too.

## Morning routine

1. Find incomplete todos due yesterday.
2. Carry them over to today.
3. Add default daily todos if missing.
4. Generate a digest.

## Requirements

- macOS
- Reminders automation permission for `osascript`
- Python 3
