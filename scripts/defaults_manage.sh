#!/bin/bash
# defaults_manage.sh - Manage default (recurring) todos
# Usage: ./defaults_manage.sh list|add "task"|remove INDEX

DATA_DIR="$(dirname "$0")/../data"
DEFAULTS_FILE="$DATA_DIR/defaults.json"

ensure_data_dir() {
    mkdir -p "$DATA_DIR"
    if [ ! -f "$DEFAULTS_FILE" ]; then
        echo "[]" > "$DEFAULTS_FILE"
    fi
}

list_defaults() {
    ensure_data_dir
    if [ ! -s "$DEFAULTS_FILE" ] || [ "$(cat "$DEFAULTS_FILE")" = "[]" ]; then
        echo "No default todos configured."
        return
    fi
    
    echo "📝 Default Todos (added daily):"
    # Parse JSON and list items
    python3 -c "
import json
import sys
try:
    with open('$DEFAULTS_FILE', 'r') as f:
        defaults = json.load(f)
    for i, d in enumerate(defaults, 1):
        print(f'  {i}. {d[\"title\"]}')
except Exception as e:
    print(f'Error: {e}')
    sys.exit(1)
"
}

add_default() {
    local task="$1"
    ensure_data_dir
    
    python3 -c "
import json
import sys
import uuid

defaults = []
try:
    with open('$DEFAULTS_FILE', 'r') as f:
        defaults = json.load(f)
except:
    pass

defaults.append({
    'id': str(uuid.uuid4())[:8],
    'title': '''$task''',
    'created_at': __import__('datetime').datetime.now().isoformat()
})

with open('$DEFAULTS_FILE', 'w') as f:
    json.dump(defaults, f, indent=2)

print(f'Added default: $task')
"
}

remove_default() {
    local index="$1"
    ensure_data_dir
    
    python3 -c "
import json
import sys

try:
    with open('$DEFAULTS_FILE', 'r') as f:
        defaults = json.load(f)
    
    idx = int('$index') - 1  # Convert to 0-based
    if 0 <= idx < len(defaults):
        removed = defaults.pop(idx)
        with open('$DEFAULTS_FILE', 'w') as f:
            json.dump(defaults, f, indent=2)
        print(f'Removed: {removed[\"title\"]}')
    else:
        print(f'Invalid index: $index')
        sys.exit(1)
except Exception as e:
    print(f'Error: {e}')
    sys.exit(1)
"
}

case "$1" in
    list)
        list_defaults
        ;;
    add)
        if [ -z "$2" ]; then
            echo "Usage: $0 add 'task description'"
            exit 1
        fi
        add_default "$2"
        ;;
    remove)
        if [ -z "$2" ]; then
            echo "Usage: $0 remove INDEX"
            exit 1
        fi
        remove_default "$2"
        ;;
    *)
        echo "Usage: $0 {list|add 'task'|remove INDEX}"
        exit 1
        ;;
esac
