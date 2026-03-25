#!/usr/bin/osascript
-- todo_add.scpt - Add a new todo to Apple Reminders
-- Usage: osascript todo_add.scpt "Task description"

on run argv
    if (count of argv) = 0 then
        return "Error: No task provided"
    end if
    
    set taskName to item 1 of argv
    set todoId to do shell script "openssl rand -hex 4"
    set today to current date
    set time of today to 0
    
    tell application "Reminders"
        -- Ensure list exists
        if not (exists list "Daily Todos") then
            make new list with properties {name:"Daily Todos"}
        end if
        
        set reminderList to list "Daily Todos"
        
        -- Create reminder with ID in notes
        make new reminder at reminderList with properties {¬
            name:taskName, ¬
            due date:today, ¬
            body:"[ID: " & todoId & "]"¬
        }
    end tell
    
    return "Added: " & taskName & " [" & todoId & "]"
end run
