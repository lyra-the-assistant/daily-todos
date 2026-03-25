---
name: daily-todos
description: Daily todo management with Apple Reminders and slash commands. Use when the user wants to manage daily tasks via /todo add, /todo list, /todo complete commands, or set up morning todo digests with automatic reminders.
metadata:
  openclaw:
    emoji: "✅"
    os: ["darwin"]
---

# Daily Todos Skill

Daily todo management with Apple Reminders integration and slash command support.

## Slash Commands

Once configured in Gateway, these commands are available:

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

## Gateway Configuration

Add to your Gateway config to enable slash commands:

```yaml
commands:
  - name: todo
    description: Manage daily todos
    subcommands:
      - name: add
        description: Add a new todo
        arguments:
          - name: task
            description: The task to add
            required: true
      - name: list
        description: List today's todos
      - name: all
        description: List all incomplete todos
      - name: complete
        description: Complete a todo
        arguments:
          - name: id
            description: Todo ID (from list)
            required: true
      - name: default-add
        description: Add a daily recurring todo
        arguments:
          - name: task
            description: The daily task
            required: true
      - name: defaults
        description: List daily recurring todos
      - name: default-remove
        description: Remove a daily todo
        arguments:
          - name: index
            description: Index from defaults list
            required: true
      - name: morning
        description: Run morning routine (carry over + defaults)
      - name: digest
        description: Show todo digest
```

## How It Works

### Data Storage

- **Active todos**: Stored in Apple Reminders list "Daily Todos"
- **Default todos**: Stored in `~/.openclaw/skills/daily-todos/data/defaults.json`
- **Todo metadata**: Embedded in reminder notes as `[ID: xxx]`

### Morning Routine

The morning routine (run via cron or `/todo morning`):

1. Finds incomplete todos from yesterday in Apple Reminders
2. Carries them over to today (creates new reminders)
3. Adds default daily todos to today's list
4. Sends digest to configured channel

### AppleScript Implementation

All Apple Reminders operations use native AppleScript:

```applescript
tell application "Reminders"
    set reminderList to list "Daily Todos"
    make new reminder at reminderList with properties {name:task, due date:today}
end tell
```

## Scripts

Located in `scripts/`:

| Script | Purpose |
|--------|---------|
| `todo_add.scpt` | Add a todo to Apple Reminders |
| `todo_list.scpt` | List active todos |
| `todo_complete.scpt` | Mark todo as complete |
| `todo_morning.scpt` | Morning routine |
| `todo_digest.scpt` | Generate digest |
| `defaults_manage.sh` | Manage default todos (JSON) |

## Cron Setup

Schedule daily morning digest:

```bash
openclaw cron add \
  --name "daily-todos-morning" \
  --schedule "cron:0 9 * * *" \
  --timezone "Asia/Shanghai" \
  --command "Run morning todo routine and send digest to Discord"
```

Or use the skill's wrapper:

```bash
./scripts/cron_morning.sh
```

## Manual Usage

Without slash commands, use the scripts directly:

```bash
# Add todo
osascript scripts/todo_add.scpt "Review PRs"

# List todos
osascript scripts/todo_list.scpt

# Complete todo
osascript scripts/todo_complete.scpt "abc123"

# Morning routine
osascript scripts/todo_morning.scpt
```
