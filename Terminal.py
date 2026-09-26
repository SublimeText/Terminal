import sublime
import sublime_plugin
import json
import os
import shutil
import sys
import subprocess

if os.name == 'nt':
    try:
        import _winreg
    except (ImportError):
        import winreg as _winreg
    from ctypes import windll, create_unicode_buffer


class NotFoundError(Exception):
    pass


INSTALLED_DIR = __name__.split('.')[0]

# Stacks of terminal window IDs opened from each Sublime window (Linux only).
# SwitchToTerminalCommand activates the most recent live window for its opener,
# falling back to older ones when a terminal is closed.
_terminal_wid_stacks = {}


def get_setting(key, default=None):
    settings = sublime.load_settings('Terminal.sublime-settings')
    os_specific_settings = {}
    if os.name == 'nt':
        os_specific_settings = sublime.load_settings('Terminal (Windows).sublime-settings')
    elif sys.platform == 'darwin':
        os_specific_settings = sublime.load_settings('Terminal (OSX).sublime-settings')
    else:
        os_specific_settings = sublime.load_settings('Terminal (Linux).sublime-settings')
    return os_specific_settings.get(key, settings.get(key, default))


def powershell(package_dir):
    # This mimics the default powershell colors since calling
    # subprocess.POpen() ends up acting like launching powershell
    # from cmd.exe. Normally the size and color are inherited
    # from cmd.exe, but this creates a custom mapping, and then
    # the LaunchPowerShell.bat file adjusts some other settings.
    key_string = 'Console\\%SystemRoot%_system32_WindowsPowerShell_v1.0_powershell.exe'
    try:
        key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, key_string)
    except (WindowsError):
        key = _winreg.CreateKey(_winreg.HKEY_CURRENT_USER, key_string)
        _winreg.SetValueEx(key, 'ColorTable05', 0, _winreg.REG_DWORD, 5645313)
        _winreg.SetValueEx(key, 'ColorTable06', 0, _winreg.REG_DWORD, 15789550)
    default = os.path.join(package_dir, 'PS.bat')
    sublime_terminal_path = os.path.join(
        sublime.packages_path(), INSTALLED_DIR)
    # This should turn the path into an 8.3-style path,
    # getting around unicode issues and spaces
    buf = create_unicode_buffer(512)
    if windll.kernel32.GetShortPathNameW(sublime_terminal_path, buf, len(buf)):
        sublime_terminal_path = buf.value
    os.environ['sublime_terminal_path'] = sublime_terminal_path.replace(' ', '` ')

    return default


def linux_terminal():
    ps = 'ps -eo comm,args | grep -E "^(gnome-session|ksmserver|xfce4-session|lxsession|mate-panel|cinnamon-sessio)" | grep -v grep'  # noqa: E501
    wm = [x.replace("\n", '') for x in os.popen(ps)]
    if wm:
        # elementary OS: `/usr/lib/gnome-session/gnome-session-binary --session=pantheon`
        # Gnome: `gnome-session` or `gnome-session-binary`
        # Linux Mint Cinnamon: `cinnamon-sessio cinnamon-session --session cinnamon`
        if wm[0].startswith('gnome-session') or wm[0].startswith('cinnamon-sessio'):
            if 'pantheon' in wm[0]:
                return 'pantheon-terminal'
            return 'gnome-terminal'
        if wm[0].startswith('xfce4-session'):
            return 'xfce4-terminal'
        if wm[0].startswith('ksmserver'):
            return 'konsole'
        if wm[0].startswith('lxsession'):
            return 'lxterminal'
        if wm[0].startswith('mate-panel'):
            return 'mate-terminal'

    # nothing specific found, return a default
    return 'xterm'


def _linux_window_backend():
    if sys.platform != 'linux':
        return None
    if os.environ.get('HYPRLAND_INSTANCE_SIGNATURE') and shutil.which('hyprctl'):
        return 'hyprland'
    if shutil.which('xdotool'):
        return 'xdotool'
    return None


def _has_linux_window_tool():
    return _linux_window_backend() is not None


def _get_active_wid():
    backend = _linux_window_backend()
    try:
        if backend == 'hyprland':
            out = subprocess.check_output(
                ['hyprctl', 'activewindow', '-j'],
                timeout=2, stderr=subprocess.DEVNULL
            ).decode().strip()
            return json.loads(out).get('address')
        elif backend == 'xdotool':
            return subprocess.check_output(
                ['xdotool', 'getactivewindow'],
                timeout=2, stderr=subprocess.DEVNULL
            ).decode().strip()
    except (Exception):
        pass
    return None


def _find_wid_by_pid(pid):
    backend = _linux_window_backend()
    try:
        if backend == 'hyprland':
            for client in _hyprland_clients():
                if client.get('pid') == pid:
                    return client.get('address')
        elif backend == 'xdotool':
            result = subprocess.check_output(
                ['xdotool', 'search', '--pid', str(pid)],
                timeout=2, stderr=subprocess.DEVNULL
            ).decode().strip()
            if result:
                return result.splitlines()[-1]
    except (Exception):
        pass
    return None


def _is_window_alive(wid):
    backend = _linux_window_backend()
    try:
        if backend == 'hyprland':
            return any(c.get('address') == wid for c in _hyprland_clients())
        elif backend == 'xdotool':
            subprocess.check_output(
                ['xdotool', 'getwindowname', wid],
                timeout=2, stderr=subprocess.DEVNULL)
            return True
    except (Exception):
        pass
    return False


def _activate_window(wid):
    backend = _linux_window_backend()
    try:
        if backend == 'hyprland':
            subprocess.run(
                ['hyprctl', 'dispatch', 'focuswindow', 'address:' + wid],
                timeout=2, stderr=subprocess.DEVNULL)
        elif backend == 'xdotool':
            subprocess.run(
                ['xdotool', 'windowactivate', wid],
                timeout=2, stderr=subprocess.DEVNULL)
    except (Exception):
        pass


def _activate_by_class(class_name):
    backend = _linux_window_backend()
    try:
        if backend == 'hyprland':
            subprocess.run(
                ['hyprctl', 'dispatch', 'focuswindow', 'class:' + class_name],
                timeout=2, stderr=subprocess.DEVNULL)
        elif backend == 'xdotool':
            subprocess.run([
                'xdotool', 'search', '--class',
                class_name, 'windowactivate',
            ], timeout=2, stderr=subprocess.DEVNULL)
    except (Exception):
        pass


def _hyprland_clients():
    try:
        out = subprocess.check_output(
            ['hyprctl', 'clients', '-j'],
            timeout=2, stderr=subprocess.DEVNULL
        ).decode().strip()
        return json.loads(out)
    except (Exception):
        return []


def _hyprland_tag_window(tag, selector, add=True):
    args = ['hyprctl', 'dispatch', 'tagwindow']
    if not add:
        # Without this, hyprctl parses "-tag" as a hyprctl option.
        args.append('--')
    args.extend([('+' if add else '-') + tag, selector])
    subprocess.run(
        args, timeout=2, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)


def _remove_hyprland_tag(tag):
    for client in _hyprland_clients():
        if tag in client.get('tags', []):
            _hyprland_tag_window(
                tag, 'address:' + client.get('address'), add=False)


def _hyprland_window_ids():
    return set(
        c.get('address') for c in _hyprland_clients() if c.get('address'))


def _find_new_hyprland_wid(before_wids):
    clients = [
        c for c in _hyprland_clients()
        if c.get('address') and c.get('address') not in before_wids
    ]
    if not clients:
        return None

    active_wid = _get_active_wid()
    if active_wid in [c.get('address') for c in clients]:
        return active_wid

    clients.sort(key=lambda c: c.get('focusHistoryID', 999999))
    return clients[0].get('address')


def _sublime_opener_tag(window_id):
    return 'sublime-opener-' + str(window_id)


def _tag_sublime_window(window_id, wid):
    """Tag a specific Sublime window for Hyprland focus switching."""
    tag = _sublime_opener_tag(window_id)
    if _linux_window_backend() == 'hyprland' and wid:
        try:
            # Keep the documented generic tag best-effort, but also add a
            # window-specific tag for shells that receive it in their env.
            _remove_hyprland_tag('sublime-opener')
            _remove_hyprland_tag(tag)
            _hyprland_tag_window('sublime-opener', 'address:' + wid)
            _hyprland_tag_window(tag, 'address:' + wid)
        except (Exception):
            pass
    return tag


class TerminalSelector():
    default = None

    @staticmethod
    def get(terminal_key):
        package_dir = os.path.join(sublime.packages_path(), INSTALLED_DIR)
        terminal = get_setting(terminal_key)
        if terminal:
            path, executable = os.path.split(terminal)
            if not path:
                joined_terminal = os.path.join(package_dir, executable)
                if os.path.exists(joined_terminal):
                    terminal = joined_terminal
                    if not os.access(terminal, os.X_OK):
                        os.chmod(terminal, 0o755)
            return terminal

        if TerminalSelector.default:
            return TerminalSelector.default

        default = None

        if os.name == 'nt':
            if os.path.exists(os.environ['SYSTEMROOT'] + '\\System32\\WindowsPowerShell\\v1.0\\powershell.exe'):
                default = powershell(package_dir)
            else:
                default = os.environ['SYSTEMROOT'] + '\\System32\\cmd.exe'

        elif sys.platform == 'darwin':
            script = 'Terminal.sh'
            if get_setting('reuse_window', False):
                script = 'TerminalReuse.sh'

            default = os.path.join(package_dir, script)
            if not os.access(default, os.X_OK):
                os.chmod(default, 0o755)

        else:
            default = linux_terminal()

        TerminalSelector.default = default
        return default


class TerminalCommand():
    def get_path(self, paths):
        view = self.window.active_view()

        if paths:
            # a path has been passed to the command (ie. a context)
            return paths[0]

        if view and view.file_name():
            # check that the file actually exists on disk
            return view.file_name()

        if self.window.folders():
            # default to the first project directory, if it exists
            return self.window.folders()[0]

        # finally fall back to the user home directory
        sublime.status_message('Terminal: opening at home directory')
        return os.path.expanduser('~')

    def terminal_open(self, location, terminal, parameters):
        try:
            window_id = self.window.id()
            for k, v in enumerate(parameters):
                parameters[k] = v.replace('%CWD%', location)
            args = [TerminalSelector.get(terminal)]
            args.extend(parameters)

            # Copy over environment settings onto parent environment
            env_setting = get_setting('env', {})
            env = os.environ.copy()
            for k in env_setting:
                if env_setting[k] is None:
                    env.pop(k, None)
                else:
                    env[k] = env_setting[k]

            # On Linux, set up bidirectional focus switching.
            # Hyprland: tag Sublime's window so terminals can focus
            # back via hyprctl's tag selector. Env vars don't survive
            # single-instance terminals (e.g. Ghostty gtk-single-instance).
            # X11: inject Sublime's window ID as env var for xdotool.
            if _has_linux_window_tool():
                sublime_wid = _get_active_wid()
                if _linux_window_backend() == 'hyprland':
                    env['SUBLIME_TERMINAL_OPENER_TAG'] = _tag_sublime_window(
                        window_id, sublime_wid)
                elif sublime_wid:
                    env['SUBLIME_TERMINAL_OPENER_WID'] = sublime_wid

            before_wids = set()
            if _linux_window_backend() == 'hyprland':
                before_wids = _hyprland_window_ids()

            # Run our process
            proc = subprocess.Popen(args, cwd=location, env=env)

            # On Linux, capture the new terminal's window ID after it
            # appears and takes focus. Used by SwitchToTerminalCommand.
            if _has_linux_window_tool():
                def _capture_wid():
                    try:
                        wid = _find_wid_by_pid(proc.pid)
                        if not wid and _linux_window_backend() == 'hyprland':
                            wid = _find_new_hyprland_wid(before_wids)
                        if not wid:
                            wid = _get_active_wid()
                        stack = _terminal_wid_stacks.setdefault(window_id, [])
                        if wid and wid not in stack:
                            stack.append(wid)
                    except (Exception):
                        pass
                sublime.set_timeout(_capture_wid, 1500)

        except (OSError) as exception:
            print(str(exception))
            sublime.error_message('Terminal: The terminal ' + TerminalSelector.get(terminal) + ' was not found')
        except (Exception) as exception:
            sublime.error_message('Terminal: ' + str(exception))


class TerminalOpenCommand(sublime_plugin.WindowCommand, TerminalCommand):
    def is_visible(self, paths=[]):
        # remove the command if the view doesn't have a path to open at
        # taking is_visible over is_enabled to remove it from the context menu,
        # instead of simply disabling the entry
        view = self.window.active_view()
        return bool(view and view.file_name() or paths)

    def run(self, paths=[], parameters=None, terminal=None):
        path = self.get_path(paths)

        if terminal is None:
            terminal = 'terminal'

        if parameters is None:
            parameters = get_setting('parameters', [])

        if os.path.isfile(path):
            path = os.path.dirname(path)

        self.terminal_open(path, terminal, parameters)


class TerminalOpenProjectFolderCommand(sublime_plugin.WindowCommand, TerminalCommand):
    def is_visible(self):
        # remove the command if the current window doesn't have directories
        # i.e. it's a single file (use the other command)
        # is_visible and is_enabled effectively do the same thing here
        return bool(self.window.folders())

    def run(self, paths=[], parameters=None):
        path = self.get_path(paths)
        if not path:
            return

        # We require separator to be appended since /hello and /hello-world
        # would both match a file in `/hello` without it
        # See https://github.com/wbond/sublime_terminal/issues/86
        folders = [x for x in self.window.folders() if path.find(x + os.sep) == 0][0:1]

        command = TerminalOpenCommand(self.window)
        command.run(folders, parameters=parameters)


class TerminalSwitchCommand(sublime_plugin.WindowCommand, TerminalCommand):
    def is_visible(self):
        if sys.platform == 'darwin':
            return True
        return _has_linux_window_tool()

    def run(self, paths=[], parameters=None):
        if sys.platform == 'darwin':
            package_dir = os.path.join(sublime.packages_path(), INSTALLED_DIR)
            subprocess.run(os.path.join(package_dir, 'TerminalSwitch.sh'))
        elif sys.platform == 'linux':
            if not _has_linux_window_tool():
                sublime.error_message(
                    'Terminal: No supported window tool found.\n'
                    'For X11, install xdotool:\n'
                    '- Debian/Ubuntu/Mint: sudo apt install xdotool\n'
                    '- Arch: sudo pacman -S xdotool\n'
                    '- Fedora: sudo dnf install xdotool\n'
                    'For Hyprland, hyprctl is detected automatically.\n'
                    'Other Wayland compositors are not currently supported.')
                return

            activated = False

            # Walk the stack from most recent, prune dead windows
            stack = _terminal_wid_stacks.setdefault(self.window.id(), [])
            while stack:
                wid = stack[-1]
                if _is_window_alive(wid):
                    _activate_window(wid)
                    activated = True
                    break
                else:
                    stack.pop()

            if not activated:
                # Fallback: activate by window class
                terminal_class = get_setting('terminal_class', '')
                if not terminal_class:
                    terminal = get_setting('terminal', '') or linux_terminal()
                    terminal_class = os.path.basename(terminal)
                _activate_by_class(terminal_class)
