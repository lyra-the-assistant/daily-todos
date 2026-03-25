#!/usr/bin/osascript
-- todo_complete.scpt - Mark a todo as complete by ID
-- Usage: osascript todo_complete.scpt <todo_id>

on run argv
    if (count of argv) = 0 then
        return "Error: No todo ID provided"
    end if
    
    set searchId to item 1 of argv
    
    tell application "Reminders"
        if not (exists list "Daily Todos") then
            return "Error: List 'Daily Todos' not found"
        end if
        
        set reminderList to list "Daily Todos"
        set allReminders to reminders of reminderList whose completed is false
        
        for eachReminder in allReminders
            set notesText to body of eachReminder
            if notesText contains "[ID: " & searchId then
                set completed of eachReminder to true
                return "✅ Completed: " & (name of eachReminder)
            end if
        end for
        
        return "❌ Todo not found with ID: " & searchId
    end tell
end run
