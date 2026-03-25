#!/usr/bin/osascript
-- todo_list.scpt - List today's active todos
-- Usage: osascript todo_list.scpt

on run
    set today to current date
    set time of today to 0
    set tomorrow to today + (1 * days)
    
    tell application "Reminders"
        if not (exists list "Daily Todos") then
            return "No todos found. List 'Daily Todos' does not exist."
        end if
        
        set reminderList to list "Daily Todos"
        set allReminders to reminders of reminderList
        set activeTodos to {}
        set output to "📋 Today's Todos:" & return & return
        set counter to 1
        
        for eachReminder in allReminders
            set remDate to due date of eachReminder
            set isCompleted to completed of eachReminder
            
            if remDate ≥ today and remDate < tomorrow and not isCompleted then
                set taskName to name of eachReminder
                set notesText to body of eachReminder
                set todoId to ""
                
                -- Extract ID from notes
                if notesText contains "[ID: " then
                    set AppleScript's text item delimiters to "[ID: "
                    set temp to text item 2 of notesText
                    set AppleScript's text item delimiters to "]"
                    set todoId to text item 1 of temp
                    set AppleScript's text item delimiters to ""
                end if
                
                set output to output & counter & ". ☐ " & taskName
                if todoId ≠ "" then
                    set output to output & " `[" & todoId & "]`"
                end if
                set output to output & return
                set counter to counter + 1
            end if
        end for
        
        if counter = 1 then
            return "📋 No active todos for today!"
        end if
        
        return output
    end tell
end run
