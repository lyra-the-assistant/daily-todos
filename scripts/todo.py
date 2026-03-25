#!/usr/bin/env python3
"""Daily Todo Manager - Uses remindctl for Apple Reminders integration"""

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


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DEFAULTS_FILE):
        save_json(DEFAULTS_FILE, [])


def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def load_json(path, default=None):
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return default if default is not None else []


def run_remindctl(*args):
    """Run remindctl and return (code, stdout, stderr)"""
    cmd = ['remindctl'] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def ensure_list():
    """Ensure Daily Todos list exists"""
    rc, _, _ = run_remindctl('list', REMINDERS_LIST)
    if rc != 0:
        run_remindctl('list', REMINDERS_LIST, '--create')


def get_today():
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)


def get_tomorrow():
    return get_today() + timedelta(days=1)


def get_yesterday():
    return get_today() - timedelta(days=1)


def extract_id_from_body(body):
    """Extract todo ID from reminder body"""
    if not body:
        return None
    # Match both [ID: xxx] and [Todo ID: xxx]
    match = re.search(r'\[(?:Todo\s+)?ID:\s*([^\]]+)\]', body)
    return match.group(1) if match else None


def parse_due_date(due_str):
    """Parse due date string to datetime"""
    if not due_str:
        return None
    try:
        # Handle ISO format with Z or timezone
        if 'Z' in due_str:
            due_str = due_str.replace('Z', '+00:00')
        dt = datetime.fromisoformat(due_str)
        # Convert to local time (naive)
        if dt.tzinfo:
            import time
            tz_offset = time.timezone if time.daylight == 0 else time.altzone
            dt = dt.replace(tzinfo=None) - timedelta(seconds=tz_offset)
        return dt
    except:
        return None


def get_reminders_json(list_name=None):
    """Get reminders as JSON"""
    args = ['all', '--json']
    if list_name:
        args = ['list', list_name, '--json']
    
    rc, stdout, _ = run_remindctl(*args)
    if rc != 0:
        return []
    
    try:
        data = json.loads(stdout)
        # Convert remindctl format to our format
        reminders = []
        for item in data:
            reminders.append({
                'id': item.get('id', ''),  # remindctl internal ID
                'title': item.get('title', ''),
                'completed': item.get('isCompleted', False),
                'due': item.get('dueDate', ''),
                'notes': item.get('notes', '')
            })
        return reminders
    except json.JSONDecodeError:
        return []


def add_todo(title, due_date=None, notes_prefix=""):
    """Add a new todo"""
    ensure_list()
    
    if due_date is None:
        due_date = get_today().strftime('%Y-%m-%d')
    
    todo_id = str(uuid4())[:8]
    notes = f"{notes_prefix}[ID: {todo_id}]"
    
    run_remindctl(
        'add', title,
        '--list', REMINDERS_LIST,
        '--due', due_date,
        '--notes', notes
    )
    
    return {'id': todo_id, 'title': title, 'date': due_date}


def cmd_add(args):
    """Add a todo"""
    due = args.due if args.due else get_today().strftime('%Y-%m-%d')
    todo = add_todo(args.title, due)
    print(f"Added: {todo['title']} [{todo['id']}]")


def cmd_list(_args=None):
    """List today's todos"""
    reminders = get_reminders_json(REMINDERS_LIST)
    
    today = get_today()
    tomorrow = get_tomorrow()
    
    active = []
    for r in reminders:
        if r.get('completed'):
            continue
        due = parse_due_date(r.get('due'))
        if not due:
            continue
        if today <= due < tomorrow:
            todo_id = extract_id_from_body(r.get('notes', ''))
            active.append({
                'title': r['title'],
                'id': todo_id or 'N/A',
                'due': r.get('due', '')
            })
    
    if not active:
        print("No active todos for today!")
        return
    
    print("Today's Todos:")
    print()
    for i, todo in enumerate(active, 1):
        print(f"  {i}. [ ] {todo['title']} [{todo['id']}]")


def cmd_all(_args=None):
    """List all incomplete todos"""
    reminders = get_reminders_json(REMINDERS_LIST)
    
    incomplete = [r for r in reminders if not r.get('completed')]
    
    if not incomplete:
        print("All caught up! No incomplete todos.")
        return
    
    print("All Incomplete Todos:")
    print()
    for i, r in enumerate(incomplete, 1):
        todo_id = extract_id_from_body(r.get('notes', ''))
        due_str = r.get('due', 'No date')
        if due_str and 'T' in due_str:
            due_str = due_str.split('T')[0]
        print(f"  {i}. {r['title']} ({due_str}) [{todo_id or 'N/A'}]")


def cmd_complete(args):
    """Complete a todo by ID"""
    reminders = get_reminders_json(REMINDERS_LIST)
    
    for r in reminders:
        todo_id = extract_id_from_body(r.get('notes', ''))
        if todo_id and todo_id.startswith(args.id):
            # Use remindctl's ID to complete
            rc, stdout, stderr = run_remindctl('complete', r['id'])
            if rc == 0:
                print(f"Completed: {r['title']}")
            else:
                print(f"Error completing: {stderr}")
            return
    
    print(f"Todo not found with ID: {args.id}")
    sys.exit(1)


def cmd_morning(_args=None):
    """Morning routine"""
    ensure_list()
    
    today = get_today()
    yesterday = get_yesterday()
    tomorrow = get_tomorrow()
    
    reminders = get_reminders_json(REMINDERS_LIST)
    
    carried = 0
    defaults_added = 0
    
    # Carry over incomplete from yesterday
    for r in reminders:
        if r.get('completed'):
            continue
        due = parse_due_date(r.get('due'))
        if not due:
            continue
        if yesterday <= due < today:
            # Carry over
            add_todo(r['title'], today.strftime('%Y-%m-%d'), '[Carried] ')
            carried += 1
    
    # Add default todos
    ensure_data_dir()
    defaults = load_json(DEFAULTS_FILE, [])
    
    # Check existing today
    today_titles = set()
    for r in reminders:
        if r.get('completed'):
            continue
        due = parse_due_date(r.get('due'))
        if not due:
            continue
        if today <= due < tomorrow:
            today_titles.add(r['title'])
    
    for d in defaults:
        if d['title'] not in today_titles:
            add_todo(d['title'], today.strftime('%Y-%m-%d'), '[Default] ')
            defaults_added += 1
    
    print(f"Morning routine complete!")
    print(f"Carried over: {carried}")
    print(f"Defaults added: {defaults_added}")


def cmd_digest(_args=None):
    """Generate digest"""
    reminders = get_reminders_json(REMINDERS_LIST)
    
    today = get_today()
    yesterday = get_yesterday()
    tomorrow = get_tomorrow()
    
    active_today = []
    completed_today = []
    incomplete_yesterday = []
    
    for r in reminders:
        due = parse_due_date(r.get('due'))
        if not due:
            continue
        todo_id = extract_id_from_body(r.get('notes', ''))
        
        if today <= due < tomorrow:
            if r.get('completed'):
                completed_today.append(r['title'])
            else:
                active_today.append({'title': r['title'], 'id': todo_id})
        elif yesterday <= due < today and not r.get('completed'):
            incomplete_yesterday.append(r['title'])
    
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
    """Add a default todo"""
    ensure_data_dir()
    defaults = load_json(DEFAULTS_FILE, [])
    
    new_default = {
        'id': str(uuid4())[:8],
        'title': args.title,
        'created_at': datetime.now().isoformat()
    }
    defaults.append(new_default)
    save_json(DEFAULTS_FILE, defaults)
    
    print(f"Added default: {args.title}")


def cmd_defaults(_args=None):
    """List default todos"""
    ensure_data_dir()
    defaults = load_json(DEFAULTS_FILE, [])
    
    if not defaults:
        print("No default todos configured.")
        return
    
    print("Default Todos (added daily):")
    for i, d in enumerate(defaults, 1):
        print(f"  {i}. {d['title']}")


def cmd_default_remove(args):
    """Remove a default todo"""
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
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Add
    add_p = subparsers.add_parser('add', help='Add a new todo')
    add_p.add_argument('title', help='Todo title')
    add_p.add_argument('--due', help='Due date (YYYY-MM-DD)')
    
    # List
    subparsers.add_parser('list', help='List today\'s todos')
    
    # All
    subparsers.add_parser('all', help='List all incomplete todos')
    
    # Complete
    comp_p = subparsers.add_parser('complete', help='Complete a todo')
    comp_p.add_argument('id', help='Todo ID')
    
    # Morning
    subparsers.add_parser('morning', help='Run morning routine')
    
    # Digest
    subparsers.add_parser('digest', help='Show digest')
    
    # Default add
    def_add_p = subparsers.add_parser('default-add', help='Add a default todo')
    def_add_p.add_argument('title', help='Default todo title')
    
    # Defaults
    subparsers.add_parser('defaults', help='List default todos')
    
    # Default remove
    def_rem_p = subparsers.add_parser('default-remove', help='Remove a default todo')
    def_rem_p.add_argument('index', type=int, help='Index from defaults list')
    
    args = parser.parse_args()
    
    cmds = {
        'add': cmd_add,
        'list': cmd_list,
        'all': cmd_all,
        'complete': cmd_complete,
        'morning': cmd_morning,
        'digest': cmd_digest,
        'default-add': cmd_default_add,
        'defaults': cmd_defaults,
        'default-remove': cmd_default_remove,
    }
    
    if args.command in cmds:
        cmds[args.command](args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
