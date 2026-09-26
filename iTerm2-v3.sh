#!/bin/bash

CD_CMD="cd "\\\"$(pwd)\\\"" && clear"
if echo "$SHELL" | grep -E "/fish$" &> /dev/null; then
	CD_CMD="cd "\\\"$(pwd)\\\""; and clear"
fi
VERSION=$(sw_vers -productVersion)
OPEN_IN_TAB=0
ITERM_APPLICATION="iTerm"

if osascript -e 'id of application "iTerm2"' >/dev/null 2>&1; then
	ITERM_APPLICATION="iTerm2"
fi

while [ "$1" != "" ]; do
	PARAM="$1"
	VALUE="$2"
	case "$PARAM" in
		--open-in-tab)
			OPEN_IN_TAB=1
			;;
	esac
	shift
done

RUNNING=$(osascript<<END
tell application "System Events"
	count(processes whose name is "$ITERM_APPLICATION")
end tell
END
)

if (( $RUNNING == 0 )); then
	osascript<<END
	tell application "$ITERM_APPLICATION"
		tell current window
            activate
			tell current session
				write text "$CD_CMD"
			end tell
		end tell
	end tell
END
osascript<<END
	tell application "$ITERM_APPLICATION"
		tell current window
            activate
			tell current session
				write text "$CD_CMD"
			end tell
		end tell
	end tell
END
else
	if (( $OPEN_IN_TAB )); then
		osascript &>/dev/null <<EOF
		tell application "$ITERM_APPLICATION"
			if (count of windows) = 0 then
				set theWindow to (create window with default profile)
				set theSession to current session of theWindow
			else
				set theWindow to current window
				tell current window
					set theTab to create tab with default profile
					set theSession to current session of theTab
				end tell
			end if
			tell theSession
				write text "$CD_CMD"
			end tell
			activate
		end tell
EOF
	else
		osascript &>/dev/null <<EOF
		tell application "$ITERM_APPLICATION"
			tell (create window with default profile)
				tell the current session
					write text "$CD_CMD"
				end tell
			end tell
			activate
		end tell
EOF
	fi
fi
