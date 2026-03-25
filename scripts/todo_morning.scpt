#!/usr/bin/osascript
-- todo_morning.scpt - Morning routine: carry over incomplete + add defaults
-- Usage: osascript todo_morning.scpt

on run
    set today to current date
    set time of today to 0
    set yesterday to today - (1 * days)
    set tomorrow to today + (1 * days)
    
    set carriedOver to 0
    set defaultsAdded to 0
    
    tell application "Reminders"
        -- Ensure list exists
        if not (exists list "Daily Todos") then
            make new list with properties {name:"Daily Todos"}
        end if
        
        set reminderList to list "Daily Todos"
        set allReminders to reminders of reminderList
        
        -- Find yesterday's incomplete and carry over
        for eachReminder in allReminders
            set remDate to due date of eachReminder
            set isCompleted to completed of eachReminder
            
            if remDate ≥ yesterday and remDate < today and not isCompleted then
                set taskName to name of eachReminder
                set newId to do shell script "openssl rand -hex 4"
                
                make new reminder at reminderList with properties {¬
                    name:taskName, ¬
                    due date:today, ¬
                    body:"[ID: " & newId & "] [Carried from yesterday]"¬
                }
                
                set carriedOver to carriedOver + 1
            end if
        end for
    end tell
    
    -- Add default todos from JSON file
    try
        set defaultsPath to (do shell script "echo $HOME") & "/.openclaw/workspace/skills/daily-todos/data/defaults.json"
        set defaultsContent to do shell script "cat " & quoted form of defaultsPath & " 2>/dev/null || echo '[]'"
        set defaultsList to {}
        
        -- Simple JSON parsing (assumes simple array format)
        if defaultsContent contains "title" then
            set AppleScript's text item delimiters to "{\"title\": \""
            set itemsList to text items 2 thru -1 of defaultsContent
            set AppleScript's text item delimiters to ""
            
            for eachItem in itemsList
                set AppleScript's text item delimiters to "\""
                set taskName to text item 1 of eachItem
                set AppleScript's text item delimiters to ""
                
                if taskName ≠ "" and taskName ≠ "[" and taskName ≠ "]" then
                    -- Check if already exists for today
                    set existsToday to false
                    
                    tell application "Reminders"
                        set todayReminders to reminders of reminderList whose due date ≥ today and due date < tomorrow
                        for tr in todayReminders
                            if name of tr = taskName then
                                set existsToday to true
                                exit repeat
                            end if
                        end for
                        
                        if not existsToday then
                            set newId to do shell script "openssl rand -hex 4"
                            make new reminder at reminderList with properties {¬
                                name:taskName, ¬
                                due date:today, ¬
                                body:"[ID: " & newId & "] [Default]"¬
                            }
                            set defaultsAdded to defaultsAdded + 1
                        end if
                    end tell
                end if
            end repeat
        end if
    on error
        -- No defaults file or error reading it
    end try
    
    return "🌅 Morning routine complete!" & return & "📥 Carried over: " & carriedOver & return & "📝 Defaults added: " & defaultsAdded
end run
