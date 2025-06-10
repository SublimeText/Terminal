#!/bin/bash

CD_CMD="cd "\\\"$(pwd)\\\"" && clear"

osascript<<END
try
	tell application "System Events"
		if (count(processes whose name is "Terminal")) is 0 then
			tell application "Terminal"
				activate
				delay 0.1
				set miniaturized of window 1 to false
				delay 0.1
				do script "$CD_CMD" in window 1
			end tell
		else
			tell application "Terminal"
				activate
				delay 0.2
				do script "$CD_CMD"
			end tell
		end if
	end tell
end try
END
