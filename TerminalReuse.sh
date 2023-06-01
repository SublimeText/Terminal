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
		tell application "Terminal"
			do script "$CD_CMD" in window 1
		end tell
	end tell
end try
END
