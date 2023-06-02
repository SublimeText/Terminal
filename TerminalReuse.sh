#!/bin/bash

CD_CMD="cd "\\\"$(pwd)\\\"""
if echo "$SHELL" | grep -E "/fish$" &> /dev/null; then
	CD_CMD="cd "\\\"$(pwd)\\\"""
fi

osascript<<END
try
	tell application "System Events"
		tell application "Terminal"
			activate
		end tell

		if not (exists (window 1 of process "Terminal")) then
			tell application "Terminal"
				do script "" -- opens a new window
			end tell
		end if

		tell application "Terminal"
			set miniaturized of window 1 to false
			do script "$CD_CMD" in window 1
		end tell
	end tell
end try
END
