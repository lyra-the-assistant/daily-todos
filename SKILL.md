---
name: daily-todos
description: Daily todo management with Apple Reminders sync and slash commands. Use when the user wants to manage daily tasks via /todo add, /todo list, /todo complete commands, or set up automated morning digests.
metadata:
  openclaw:
    emoji: "✅"
    os: ["darwin"]
    requires:
      bins: ["remindctl"]
---

# Daily Todos Skill

Daily todo management with Apple Reminders integration.

## Slash Commands (via OpenClaw)

| Command | Description |
|---------|-------------|
| `/todo add <task>` | Add a new todo for today |
| `/todo list` | List today's active todos |
| `/todo all` | List all incomplete todos |
| `/todo complete <id>` | Mark a todo as complete |
| `/todo default-add <task>` | Add a daily recurring todo |
| `/todo defaults` | List default (daily) todos |
| `/todo default-remove <index>` | Remove a default todo |
| `/todo morning` | Run morning routine manually |
| `/todo digest` | Show today's todo digest |

## Scripts

Located in `scripts/`:

```bash
# Add a todo
python3 scripts/todo.py add "Task description"

# List today's todos
python3 scripts/todo.py list

# List all incomplete
python3 scripts/todo.py all

# Complete a todo
python3 scripts/todo.py complete <id>

# Morning routine (carry over + defaults)
python3 scripts/todo.py morning

# Show digest
python3 scripts/todo.py digest

# Manage defaults
python3 scripts/todo.py default-add "Daily task"
python3 scripts/todo.py defaults
python3 scripts/todo.py default-remove <index>
```

## Data Storage

- **Active todos**: Apple Reminders list "Daily Todos"
- **Default todos**: `data/defaults.json`
- **Todo metadata**: Embedded in reminder body as `[ID: xxx]`

## How It Works

### Morning Routine

1. Finds incomplete todos from yesterday
2. Carries them over to today
3. Adds default daily todos
4. Generates and sends digest

### Default Todos

Stored in `data/defaults.json` and automatically added each morning:

```json
[
  {"id": "abc123", "title": "Check email"},
  {"id": "def456", "title": "Review calendar"}
]
```

## Cron Setup

Schedule daily morning digest at 9:00 AM:

```bash
openclaw cron add \
  --name "daily-todos-morning" \
  --schedule "cron:0 9 * * *" \
  --timezone "Asia/Shanghai" \
  --command "python3 ~/.openclaw/workspace/skills/daily-todos/scripts/todo.py morning && python3 ~/.openclaw/workspace/skills/daily-todos/scripts/todo.py digest"
```

## Requirements

- macOS with Reminders access
- `remindctl` (`brew install steipete/tap/remindctl`)
- Python 3
