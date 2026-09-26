# Terminal package for Sublime Text

Shortcuts and menu entries for opening a terminal at the current file, or any directory in [Sublime Text](http://sublimetext.com/).

Note that as of build 4213 Sublime Text itself has a `open_terminal` command. It has a `terminal_command` setting, and takes a `dir` argument. It can be used for instance in keybindings as follows, and might suit your needs as well as this package does:

```json
[
  { "keys": ["super+ctrl+t"], "command": "open_terminal", "args": {"dir": "$file_path"} },
  { "keys": ["super+ctrl+alt+t"], "command": "open_terminal", "args": {"dir": "$folder"} },
]
```

## Installation

Download [Package Control](https://packages.sublimetext.com/) and use the *Package Control: Install Package* command from the command palette. Using Package Control ensures Terminal will stay up to date automatically.

## Usage

- **Open Terminal at File**
  Opens a terminal in the folder containing the currently opened file.  
- **Open Terminal at Project Folder**
  Opens a terminal in the project folder containing the currently opened file.  
- **Switch to Terminal**
  Switches focus to the most recently opened terminal window.
  Available on macOS (via AppleScript) and Linux
  ([xdotool](https://github.com/jordansissel/xdotool) on X11,
  [hyprctl](https://wiki.hyprland.org/) on Hyprland;
  other Wayland compositors are not currently supported).
  Not currently supported on Windows.

  On Linux with X11, xdotool must be installed:

  - Debian/Ubuntu/Mint: `sudo apt install xdotool`
  - Arch: `sudo pacman -S xdotool`
  - Fedora: `sudo dnf install xdotool`

  On Hyprland, `hyprctl` is detected automatically (no extra install needed).



Terminals can be opened via the command palette, the editor context menu and the sidebar context menus. Additionally, you can set up key bindings.

### Key bindings

To create keyboard shortcuts, open the *Preferences > Package Settings > Terminal > Key Bindings* menu entry. Our suggested key bindings are on the left, you can copy these over to your personal bindings on the right and tweak them to your liking. Example:

```json
[
  { "keys": ["ctrl+shift+t"], "command": "terminal_open" },
  { "keys": ["ctrl+alt+t"], "command": "terminal_open_project_folder" },
  { "keys": ["ctrl+shift+alt+t"], "command": "terminal_switch" }
]
```

#### Terminal 2.0

Note that in version 2 of this package, we stopped enabling these bindings by default. They conflicted with built-in bindings of Sublime Text, and users might have different preferences.

#### Terminal 3.0

In version 3 of this package the commands have been renamed, to avoid conflict with Sublime Text's new built-in `open_terminal` command (as of build 4213).

- `open_terminal` to `terminal_open`
- `open_terminal_project_folder` to `terminal_open_project_folder`
- `switch_to_terminal` to `terminal_switch`


## Package Settings

The settings can be viewed and edited by accessing the *Preferences > Package Settings > Terminal > Settings* menu entry. 

 - **terminal**
     - The terminal to execute, will default to the OS default if not set.
     - Default: `null`
 - **parameters**
     - The parameters to pass to the terminal. These parameters will be used if no [custom parameters](#custom-parameters) are passed.
     - Default: `[]`
 - **env**
     - The environment variables changeset. Default environment variables used when invoking the terminal are inherited from Sublime Text.
     - The changeset may be used to overwrite/unset environment variables. Use `null` to indicate that the environment variable should be unset.
     - Default: `{}`
 - **terminal_class**
     - The WM_CLASS of the terminal, used by "Switch to Terminal" on Linux. If blank, derived from the `terminal` setting. Override this if your terminal's WM_CLASS differs from its executable name. Find yours with: `xdotool getactivewindow getwindowclassname`
     - Default: `null`

## Custom Parameters

By passing parameters argument to the `terminal_open` or `terminal_open_project_folder` commands, it is possible to construct custom terminal environments. You can do so by creating custom [key bindings](https://www.sublimetext.com/docs/key_bindings.html) that call these commands with the arguments you want, as we'll document here, or by adding custom [command palette](https://docs.sublimetext.io/reference/command_palette.html) or [menu entries](https://docs.sublimetext.io/reference/menus.html).

The following is an example, of passing the parameters `-T 'Custom Window Title'`` to an XFCE terminal.

```json
{
 "keys": ["ctrl+alt+t"],
 "command": "terminal_open",
 "args": {
   "parameters": ["-T", "Custom Window Title"]
 }
}
```

A parameter may also contain the *%CWD%* placeholder, which will be substituted with the current working directory the terminal was opened to.

```json
{
 "keys": ["ctrl+alt+t"],
 "command": "terminal_open",
 "args": {
   "parameters": ["-T", "Working in directory %CWD%"]
 }
}
```

### Switching between Sublime Text and a terminal (Linux)

1. **Switching from Sublime to terminal**

    The "Switch to Terminal" command activates the most recently opened
    terminal window that was opened from within Sublime Text (externally
    launched terminals are not tracked). All terminals opened from Sublime
    are tracked; the most recent live one is activated first. If it has
    been closed, the command falls back to older ones. If no tracked
    windows remain, it searches by window class as a final fallback.

2. **Switching from terminal to Sublime**

    To switch focus back from the terminal to Sublime, add a shell key
    binding to your `~/.bashrc` (the plugin cannot register bindings
    inside external terminals):

    For X11 (xdotool):

    ```bash
    # ~/.bashrc
    if [ -n "$SUBLIME_TERMINAL_OPENER_WID" ]; then
        bind -x '"\C-]": "xdotool windowactivate $SUBLIME_TERMINAL_OPENER_WID"'
    fi
    ```

    On X11, the plugin injects `SUBLIME_TERMINAL_OPENER_WID` into the
    terminal's environment with Sublime's window ID.

    For Hyprland (Wayland):

    ```bash
    # ~/.bashrc
    sublime_terminal_focus_opener() {
        hyprctl dispatch focuswindow "tag:$SUBLIME_TERMINAL_OPENER_TAG" \
            >/dev/null 2>&1
    }

    if [ -n "$SUBLIME_TERMINAL_OPENER_TAG" ]; then
        bind -x '"\C-]": sublime_terminal_focus_opener'
    fi
    ```

    On Hyprland, the plugin tags Sublime's opener window and injects
    `SUBLIME_TERMINAL_OPENER_TAG` into the terminal environment.

    Here `\C-]` refers to `Ctrl+]`. The key binding is arbitrary and
    easy to change (see
    [here](https://www.gnu.org/software/bash/manual/html_node/Readline-Init-File-Syntax.html)
    or [here](https://www.gnu.org/software/bash/manual/html_node/Bash-Builtins.html)).

#### Troubleshooting

Some Hyprland or Wayland terminals may inherit the working directory from an
existing terminal window instead of using the cwd passed by Sublime. If a new
terminal opens in a previous shell directory, configure the terminal to accept
an explicit working directory argument.

For example, Ghostty on Hyprland can be configured as:

```json
{
  "terminal": "ghostty",
  "parameters": [
    "--gtk-single-instance=false",
    "--window-inherit-working-directory=false",
    "--working-directory=%CWD%"
  ],
  "terminal_class": "com.mitchellh.ghostty"
}
```

## Example configurations

Here are some example configurations calling different terminals. Note that paths to executables might differ on your machine.

### Cmder on Windows

```json
{
  "terminal": "C:\\Program Files\\cmder_mini\\cmder.exe",
  "parameters": ["/START", "%CWD%"]
}
```

### GNU/Linux

#### xterm

```json
{
  "terminal": "xterm"
}
```

#### gnome-terminal (CJK users)

We unset LD_PRELOAD, as it may cause problems for Sublime Text with imfix.

```json
{
  "terminal": "gnome-terminal",
  "env": {"LD_PRELOAD": null}
}
```

#### Ghostty, Kitty, WezTerm, Alacritty

Modern terminals that support GPU-accelerated rendering and 24-bit true color:

```json
{
  "terminal": "ghostty"
  // "terminal": "kitty"
  // "terminal": "wezterm"
  // "terminal": "alacritty"
}
```

### iTerm on MacOS.

```json
{
  "terminal": "iTerm.sh"
}
```

### iTerm on MacOS. with tabs

```json
{
  "terminal": "iTerm.sh",
  "parameters": ["--open-in-tab"]
}
```

### iTerm2 v3 on MacOS.

```json
{
  "terminal": "iTerm2-v3.sh"
}
```

### Hyper on MacOS.

```json
{
  "terminal": "hyper.sh"
}
```

### Kitty on OS X

```json
{
  "terminal": "/opt/homebrew/bin/kitty",
  "parameters": ["-d", "%CWD%"]
}
```

### [Windows Terminal](https://github.com/microsoft/terminal)

```json
{
  "terminal": "C:/Users/yourusername/AppData/Local/Microsoft/WindowsApps/wt.exe",
  "parameters": ["-d", "."]
}
```
