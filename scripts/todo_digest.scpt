#!/usr/bin/osascript
-- todo_digest.scpt - Generate a digest of today's todos
-- Usage: osascript todo_digest.scpt

on run
    set today to current date
    set time of today to 0
    set tomorrow to today + (1 * days)
    set yesterday to today - (1 * days)
    
    tell application "Reminders"
        if not (exists list "Daily Todos") then
            return "📋 **Daily Todo Digest**" & return & return & "No active todos for today!"
        end if
        
        set reminderList to list "Daily Todos"
        set allReminders to reminders of reminderList
        
        set activeToday to {}
        set completedToday to {}
        set incompleteYesterday to {}
        
        for eachReminder in allReminders
            set remDate to due date of eachReminder
            set isCompleted to completed of eachReminder
            set taskName to name of eachReminder
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
            
            -- Categorize
            if remDate ≥ today and remDate < tomorrow then
                if isCompleted then
                    set end of completedToday to taskName
                else
                    set end of activeToday to {taskName, todoId}
                end if
            else if remDate ≥ yesterday and remDate < today and not isCompleted then
                set end of incompleteYesterday to taskName
            end if
        end for
        
        -- Build output
        set output to "📋 **Daily Todo Digest**" & return & return
        
        -- Active todos
        set output to output & "**Today's Todos:**" & return
        if (count of activeToday) > 0 then
            set i to 1
            repeat with todoItem in activeToday
                set output to output & "  " & i & ". ☐ " & (item 1 of todoItem)
                if (item 2 of todoItem) ≠ "" then
                    set output to output & " `" & (item 2 of todoItem) & "`"
                end if
                set output to output & return
                set i to i + 1
            end repeat
        else
            set output to output & "  No active todos for today!" & return
        end if
        set output to output & return
        
        -- Completed today
        if (count of completedToday) > 0 then
            set output to output & "**Completed Today:**" & return
            repeat with taskName in completedToday
                set output to output & "  ✅ " & taskName & return
            end repeat
            set output to output & return
        end if
        
        -- Incomplete from yesterday
        if (count of incompleteYesterday) > 0 then
            set output to output & "⚠️ **Incomplete from Yesterday:**" & return
            repeat with taskName in incompleteYesterday
                set output to output & "  • " & taskName & return
            end repeat
            set output to output & return
        end if
        
        -- Stats
        set total to (count of activeToday) + (count of completedToday)
        set done to count of completedToday
        set percent to 0
        if total > 0 then
            set percent to (done / total) * 100
        end if
        set output to output & "**Progress:** " & done & "/" & total & " completed (" & (round percent) & "%)"
        
        return output
    end tell
end run
