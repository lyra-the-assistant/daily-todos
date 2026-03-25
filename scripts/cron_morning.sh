#!/bin/bash
# cron_morning.sh - Wrapper for cron morning routine with Discord output
# This script runs the morning routine and outputs for Discord

SKILL_DIR="$(dirname "$0")/.."

# Run morning routine
OUTPUT=$(osascript "$SKILL_DIR/scripts/todo_morning.scpt" 2>&1)

# Get digest
DIGEST=$(osascript "$SKILL_DIR/scripts/todo_digest.scpt" 2>&1)

# Output for Discord
echo "$OUTPUT"
echo ""
echo "$DIGEST"
echo ""
echo "What new todos do you have for today?"
