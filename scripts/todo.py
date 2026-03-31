#!/usr/bin/env python3
"""Daily Todo Manager - Uses native macOS Reminders automation via AppleScript."""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from uuid import uuid4

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "data")
DEFAULTS_FILE = os.path.join(DATA_DIR, "defaults.json")
REMINDERS_LIST = "Daily Todos"
FIELD_SEP = chr(31)
ROW_SEP = chr(30)


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DEFAULTS_FILE):
        save_json(DEFAULTS_FILE, [])


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_json(path, default=None):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default if default is not None else []


def run_applescript(script, args=None, timeout=90):
    cmd = ["osascript", "-e", script]
    if args:
        cmd.append("--")
        cmd.extend(str(a) for a in args)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip() or "osascript failed")
    return result.stdout.strip()


def ensure_list():
    script = """
on run argv
	set listName to item 1 of argv
	with timeout of 300 seconds
		tell application \"Reminders\"
			if not (exists list listName) then
				make new list with properties {name:listName}
			end if
		end tell
	end timeout
end run
"""
    run_applescript(script, [REMINDERS_LIST])


def get_today():
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)


def get_tomorrow():
    return get_today() + timedelta(days=1)


def get_yesterday():
    return get_today() - timedelta(days=1)


def extract_id_from_body(body):
    if not body:
        return None
    match = re.search(r"\[(?:Todo\s+)?ID:\s*([^\]]+)\]", body)
    return match.group(1) if match else None


def parse_due_date(due_str):
    if not due_str:
        return None
    try:
        return datetime.fromisoformat(due_str)
    except Exception:
        return None


def get_reminders_json(list_name=None):
    target_list = list_name or REMINDERS_LIST
    script = """
on pad2(n)
	set n to n as integer
	if n < 10 then return \"0\" & (n as text)
	return n as text
end pad2

on monthNumber(m)
	set monthNames to {January, February, March, April, May, June, July, August, September, October, November, December}
	repeat with i from 1 to count monthNames
		if m is item i of monthNames then return i
	end repeat
	return 0
end monthNumber

on isoText(d)
	if d is missing value then return \"\"
	set y to year of d as text
	set mo to my pad2(my monthNumber(month of d))
	set da to my pad2(day of d)
	set hh to my pad2(hours of d)
	set mm to my pad2(minutes of d)
	set ss to my pad2(seconds of d)
	return y & \"-\" & mo & \"-\" & da & \"T\" & hh & \":\" & mm & \":\" & ss
end isoText

on boolText(v)
	if v then return \"true\"
	return \"false\"
end boolText

on safeText(v)
	if v is missing value then return \"\"
	return v as text
end safeText

on run argv
	set listName to item 1 of argv
	set fieldSep to character id 31
	set rowSep to character id 30
	set rows to {}
	with timeout of 300 seconds
		tell application \"Reminders\"
			if not (exists list listName) then return \"\"
			set reminderItems to reminders of list listName
			repeat with r in reminderItems
				set rid to id of r as text
				set rname to name of r as text
				set rcompleted to my boolText(completed of r)
				set rdue to my isoText(due date of r)
				set rbody to my safeText(body of r)
				set oldTIDs to AppleScript's text item delimiters
				set AppleScript's text item delimiters to fieldSep
				set end of rows to {rid, rname, rcompleted, rdue, rbody} as text
				set AppleScript's text item delimiters to oldTIDs
			end repeat
		end tell
	end timeout
	set oldTIDs to AppleScript's text item delimiters
	set AppleScript's text item delimiters to rowSep
	set outputText to rows as text
	set AppleScript's text item delimiters to oldTIDs
	return outputText
end run
"""
    stdout = run_applescript(script, [target_list])
    if not stdout:
        return []

    reminders = []
    for row in stdout.split(ROW_SEP):
        if not row:
            continue
        parts = row.split(FIELD_SEP)
        if len(parts) != 5:
            continue
        native_id, title, completed_text, due, notes = parts
        reminders.append(
            {
                "id": native_id,
                "title": title,
                "completed": completed_text.lower() == "true",
                "due": due,
                "notes": notes,
            }
        )
    return reminders


def add_todo(title, due_date=None, notes_prefix=""):
    ensure_list()

    due_dt = datetime.strptime(due_date or get_today().strftime("%Y-%m-%d"), "%Y-%m-%d")
    due_dt = due_dt.replace(hour=9, minute=0, second=0, microsecond=0)

    todo_id = str(uuid4())[:8]
    notes = f"{notes_prefix}[ID: {todo_id}]"

    script = """
on monthEnum(monthIndex)
	return item (monthIndex as integer) of {January, February, March, April, May, June, July, August, September, October, November, December}
end monthEnum

on run argv
	set listName to item 1 of argv
	set reminderName to item 2 of argv
	set reminderBody to item 3 of argv
	set yy to (item 4 of argv) as integer
	set mo to (item 5 of argv) as integer
	set dd to (item 6 of argv) as integer
	set hh to (item 7 of argv) as integer
	set mi to (item 8 of argv) as integer
	set ss to (item 9 of argv) as integer

	set dueDate to current date
	set year of dueDate to yy
	set month of dueDate to my monthEnum(mo)
	set day of dueDate to dd
	set time of dueDate to (hh * hours + mi * minutes + ss)

	with timeout of 300 seconds
		tell application \"Reminders\"
			if not (exists list listName) then
				make new list with properties {name:listName}
			end if
			tell list listName
				make new reminder at end of reminders with properties {name:reminderName, body:reminderBody, due date:dueDate}
			end tell
		end tell
	end timeout
end run
"""
    run_applescript(
        script,
        [
            REMINDERS_LIST,
            title,
            notes,
            due_dt.year,
            due_dt.month,
            due_dt.day,
            due_dt.hour,
            due_dt.minute,
            due_dt.second,
        ],
    )

    return {"id": todo_id, "title": title, "date": due_dt.strftime("%Y-%m-%d")}


def complete_todo_by_native_id(native_id, list_name=REMINDERS_LIST):
    script = """
on run argv
	set listName to item 1 of argv
	set reminderId to item 2 of argv
	with timeout of 300 seconds
		tell application \"Reminders\"
			set targetReminder to first reminder of list listName whose id is reminderId
			set completed of targetReminder to true
			set completion date of targetReminder to current date
		end tell
	end timeout
end run
"""
    run_applescript(script, [list_name, native_id])


def delete_todo_by_native_id(native_id, list_name=REMINDERS_LIST):
    script = """
on run argv
	set listName to item 1 of argv
	set reminderId to item 2 of argv
	with timeout of 300 seconds
		tell application \"Reminders\"
			set targetReminder to first reminder of list listName whose id is reminderId
			delete targetReminder
		end tell
	end timeout
end run
"""
    run_applescript(script, [list_name, native_id])


def cmd_add(args):
    due = args.due if args.due else get_today().strftime("%Y-%m-%d")
    todo = add_todo(args.title, due)
    print(f"Added: {todo['title']} [{todo['id']}]")


def cmd_list(_args=None):
    reminders = get_reminders_json(REMINDERS_LIST)

    today = get_today()
    tomorrow = get_tomorrow()

    active = []
    for r in reminders:
        if r.get("completed"):
            continue
        due = parse_due_date(r.get("due"))
        if not due:
            continue
        if today <= due < tomorrow:
            todo_id = extract_id_from_body(r.get("notes", ""))
            active.append({"title": r["title"], "id": todo_id or "N/A", "due": r.get("due", "")})

    if not active:
        print("No active todos for today!")
        return

    print("Today's Todos:")
    print()
    for i, todo in enumerate(active, 1):
        print(f"  {i}. [ ] {todo['title']} [{todo['id']}]")


def cmd_all(_args=None):
    reminders = get_reminders_json(REMINDERS_LIST)

    incomplete = [r for r in reminders if not r.get("completed")]

    if not incomplete:
        print("All caught up! No incomplete todos.")
        return

    print("All Incomplete Todos:")
    print()
    for i, r in enumerate(incomplete, 1):
        todo_id = extract_id_from_body(r.get("notes", ""))
        due_str = r.get("due", "No date") or "No date"
        if "T" in due_str:
            due_str = due_str.split("T")[0]
        print(f"  {i}. {r['title']} ({due_str}) [{todo_id or 'N/A'}]")


def cmd_complete(args):
    reminders = get_reminders_json(REMINDERS_LIST)

    for r in reminders:
        todo_id = extract_id_from_body(r.get("notes", ""))
        if todo_id and todo_id.startswith(args.id):
            complete_todo_by_native_id(r["id"])
            print(f"Completed: {r['title']}")
            return

    print(f"Todo not found with ID: {args.id}")
    sys.exit(1)


def cmd_delete(args):
    reminders = get_reminders_json(REMINDERS_LIST)

    for r in reminders:
        todo_id = extract_id_from_body(r.get("notes", ""))
        if todo_id and todo_id.startswith(args.id):
            delete_todo_by_native_id(r["id"])
            print(f"Deleted: {r['title']}")
            return

    print(f"Todo not found with ID: {args.id}")
    sys.exit(1)


def cmd_clear(_args=None):
    reminders = get_reminders_json(REMINDERS_LIST)

    if not reminders:
        print("Daily Todos is already empty.")
        return

    deleted = 0
    for r in reminders:
        delete_todo_by_native_id(r["id"])
        deleted += 1

    print(f"Cleared Daily Todos: {deleted} removed")


def cmd_morning(_args=None):
    ensure_list()

    today = get_today()
    yesterday = get_yesterday()
    tomorrow = get_tomorrow()

    reminders = get_reminders_json(REMINDERS_LIST)

    carried = 0
    defaults_added = 0

    for r in reminders:
        if r.get("completed"):
            continue
        due = parse_due_date(r.get("due"))
        if not due:
            continue
        if yesterday <= due < today:
            add_todo(r["title"], today.strftime("%Y-%m-%d"), "[Carried] ")
            carried += 1

    ensure_data_dir()
    defaults = load_json(DEFAULTS_FILE, [])

    today_titles = set()
    for r in reminders:
        if r.get("completed"):
            continue
        due = parse_due_date(r.get("due"))
        if not due:
            continue
        if today <= due < tomorrow:
            today_titles.add(r["title"])

    for d in defaults:
        if d["title"] not in today_titles:
            add_todo(d["title"], today.strftime("%Y-%m-%d"), "[Default] ")
            defaults_added += 1

    print("Morning routine complete!")
    print(f"Carried over: {carried}")
    print(f"Defaults added: {defaults_added}")


def cmd_digest(_args=None):
    reminders = get_reminders_json(REMINDERS_LIST)

    today = get_today()
    yesterday = get_yesterday()
    tomorrow = get_tomorrow()

    active_today = []
    completed_today = []
    incomplete_yesterday = []

    for r in reminders:
        due = parse_due_date(r.get("due"))
        if not due:
            continue
        todo_id = extract_id_from_body(r.get("notes", ""))

        if today <= due < tomorrow:
            if r.get("completed"):
                completed_today.append(r["title"])
            else:
                active_today.append({"title": r["title"], "id": todo_id})
        elif yesterday <= due < today and not r.get("completed"):
            incomplete_yesterday.append(r["title"])

    print("Daily Todo Digest")
    print()

    print("Today's Todos:")
    if active_today:
        for i, t in enumerate(active_today, 1):
            print(f"  {i}. [ ] {t['title']} [{t['id'] or 'N/A'}]")
    else:
        print("  No active todos for today!")
    print()

    if completed_today:
        print("Completed Today:")
        for t in completed_today:
            print(f"  [x] {t}")
        print()

    if incomplete_yesterday:
        print("Incomplete from Yesterday:")
        for t in incomplete_yesterday:
            print(f"  * {t}")
        print()

    total = len(active_today) + len(completed_today)
    done = len(completed_today)
    pct = (done / total * 100) if total > 0 else 0
    print(f"Progress: {done}/{total} completed ({pct:.0f}%)")


def cmd_default_add(args):
    ensure_data_dir()
    defaults = load_json(DEFAULTS_FILE, [])

    new_default = {
        "id": str(uuid4())[:8],
        "title": args.title,
        "created_at": datetime.now().isoformat(),
    }
    defaults.append(new_default)
    save_json(DEFAULTS_FILE, defaults)

    print(f"Added default: {args.title}")


def cmd_defaults(_args=None):
    ensure_data_dir()
    defaults = load_json(DEFAULTS_FILE, [])

    if not defaults:
        print("No default todos configured.")
        return

    print("Default Todos (added daily):")
    for i, d in enumerate(defaults, 1):
        print(f"  {i}. {d['title']}")


def cmd_default_remove(args):
    ensure_data_dir()
    defaults = load_json(DEFAULTS_FILE, [])

    idx = args.index - 1
    if 0 <= idx < len(defaults):
        removed = defaults.pop(idx)
        save_json(DEFAULTS_FILE, defaults)
        print(f"Removed: {removed['title']}")
    else:
        print(f"Invalid index: {args.index}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Daily Todo Manager")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    add_p = subparsers.add_parser("add", help="Add a new todo")
    add_p.add_argument("title", help="Todo title")
    add_p.add_argument("--due", help="Due date (YYYY-MM-DD)")

    subparsers.add_parser("list", help="List today's todos")
    subparsers.add_parser("all", help="List all incomplete todos")

    comp_p = subparsers.add_parser("complete", help="Complete a todo")
    comp_p.add_argument("id", help="Todo ID")

    del_p = subparsers.add_parser("delete", help="Delete a todo")
    del_p.add_argument("id", help="Todo ID")

    subparsers.add_parser("clear", help="Delete all todos in Daily Todos")
    subparsers.add_parser("morning", help="Run morning routine")
    subparsers.add_parser("digest", help="Show digest")

    def_add_p = subparsers.add_parser("default-add", help="Add a default todo")
    def_add_p.add_argument("title", help="Default todo title")

    subparsers.add_parser("defaults", help="List default todos")

    def_rem_p = subparsers.add_parser("default-remove", help="Remove a default todo")
    def_rem_p.add_argument("index", type=int, help="Index from defaults list")

    args = parser.parse_args()

    cmds = {
        "add": cmd_add,
        "list": cmd_list,
        "all": cmd_all,
        "complete": cmd_complete,
        "delete": cmd_delete,
        "clear": cmd_clear,
        "morning": cmd_morning,
        "digest": cmd_digest,
        "default-add": cmd_default_add,
        "defaults": cmd_defaults,
        "default-remove": cmd_default_remove,
    }

    if args.command in cmds:
        cmds[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
