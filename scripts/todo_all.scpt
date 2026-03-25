#!/usr/bin/osascript
-- todo_all.scpt - List all incomplete todos
-- Usage: osascript todo_all.scpt

on run
    tell application "Reminders"
        if not (exists list "Daily Todos") then
            return "No todos found."
        end if
        
        set reminderList to list "Daily Todos"
        set allReminders to reminders of reminderList whose completed is false
        
        if (count of allReminders) = 0 then
            return "✅ All caught up! No incomplete todos."
        end if
        
        set output to "📋 All Incomplete Todos:" & return & return
        set counter to 1
        
        for eachReminder in allReminders
            set taskName to name of eachReminder
            set remDate to due date of eachReminder
            set notesText to body of eachReminder
            set todoId to ""
            
            -- Extract ID
            if notesText contains "[ID: " then
                set AppleScript's text item delimiters to "[ID: "
                set temp to text item 2 of notesText
                set AppleScript's text item delimiters to "]"
                set todoId to text item 1 of temp
                set AppleScript's text item delimiters to ""
            end if
            
            -- Format date
            set dateStr to (month of remDate as integer) & "/" & (day of remDate) & "/" & (year of remDate)
            
            set output to output & counter & ". " & taskName & " (" & dateStr & ")"
            if todoId ≠ "" then
                set output to output & " `[" & todoId & "]`"
            end if
            set output to output & return
            set counter to counter + 1
        end for
        
        return output
    end tell
end run
