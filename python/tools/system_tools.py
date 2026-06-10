import subprocess
import os
import json
import datetime
import platform
import shutil
import requests as http_requests

APPROVED_COMMANDS = [
    'ls', 'pwd', 'mkdir', 'cat', 'echo', 'date', 'whoami',
    'find', 'grep', 'wc', 'head', 'tail', 'df', 'du', 'free',
    'uname', 'uptime', 'ps', 'top', 'which', 'touch'
]

TOOL_DEFINITIONS = """
Available tools (use when user explicitly requests a computer action):
- open_url: Open a website. params: {"url": "https://..."}
- list_files: List files in a directory. params: {"path": "~/some/path"}
- read_file: Read a file. params: {"path": "~/file.txt"}
- write_file: Write/append to a file. params: {"path": "~/file.txt", "content": "text", "append": false}
- create_folder: Create a folder. params: {"path": "~/new/folder"}
- delete_file: Delete a file (with confirmation). params: {"path": "~/file.txt"}
- find_files: Search for files by name. params: {"pattern": "*.py", "path": "~/deathai"}
- run_command: Run safe terminal command. params: {"command": "ls -la"}
- web_search: Search the web. params: {"query": "search terms"}
- play_music: Play a music file. params: {"path": "~/music/file.mp3"}
- get_weather: Get Melbourne weather. params: {}
- system_info: Get system resource info. params: {}
- set_reminder: Set a reminder. params: {"message": "eat something", "minutes": 20}
- read_notes: Read your notes file. params: {}
- save_note: Save a note. params: {"note": "your note here"}
- read_progress: Read your Leetcode progress. params: {}
- open_app: Open a Windows application. params: {"app": "notepad/spotify/vscode/explorer"}
"""

# ─── File Tools ───────────────────────────────────────────────────────────────

def open_url(url):
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    subprocess.run(['cmd.exe', '/c', 'start', url])
    return f"Opened {url} in your browser"

def list_files(path='.'):
    path = os.path.expanduser(path)
    try:
        items = os.listdir(path)
        result = []
        for item in sorted(items):
            full = os.path.join(path, item)
            kind = 'DIR' if os.path.isdir(full) else 'FILE'
            try:
                size = os.path.getsize(full)
                result.append(f"[{kind}] {item} ({size} bytes)")
            except Exception:
                result.append(f"[{kind}] {item}")
        return '\n'.join(result) if result else "Empty directory"
    except Exception as e:
        return f"Error: {e}"

def read_file(path):
    path = os.path.expanduser(path)
    try:
        with open(path, 'r') as f:
            content = f.read()
        if len(content) > 3000:
            return content[:3000] + f"\n... (truncated, {len(content)} total chars)"
        return content
    except Exception as e:
        return f"Error reading {path}: {e}"

def write_file(path, content, append=False):
    path = os.path.expanduser(path)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
        mode = 'a' if append else 'w'
        with open(path, mode) as f:
            f.write(content)
        action = "Appended to" if append else "Written to"
        return f"{action} {path} ({len(content)} chars)"
    except Exception as e:
        return f"Error writing {path}: {e}"

def create_folder(path):
    path = os.path.expanduser(path)
    try:
        os.makedirs(path, exist_ok=True)
        return f"Created folder: {path}"
    except Exception as e:
        return f"Error: {e}"

def delete_file(path):
    path = os.path.expanduser(path)
    try:
        if not os.path.exists(path):
            return f"File not found: {path}"
        if os.path.isdir(path):
            return f"That's a directory. Be more specific about what to delete inside it."
        os.remove(path)
        return f"Deleted: {path}"
    except Exception as e:
        return f"Error: {e}"

def find_files(pattern='*', path='~'):
    path = os.path.expanduser(path)
    try:
        import fnmatch
        matches = []
        for root, dirs, files in os.walk(path):
            # Skip hidden and venv directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'venv' and d != '__pycache__']
            for filename in fnmatch.filter(files, pattern):
                matches.append(os.path.join(root, filename))
            if len(matches) >= 50:
                break
        if not matches:
            return f"No files matching '{pattern}' found in {path}"
        return f"Found {len(matches)} files:\n" + '\n'.join(matches[:50])
    except Exception as e:
        return f"Error: {e}"

# ─── System Tools ─────────────────────────────────────────────────────────────

def run_safe_command(command):
    parts = command.strip().split()
    if not parts or parts[0] not in APPROVED_COMMANDS:
        return f"Command '{parts[0] if parts else ''}' not in approved list."
    try:
        result = subprocess.run(parts, capture_output=True, text=True, timeout=10)
        return result.stdout or result.stderr or "Command completed with no output"
    except Exception as e:
        return f"Error: {e}"

def system_info():
    try:
        result = []
        # Memory
        mem = subprocess.run(['free', '-h'], capture_output=True, text=True)
        result.append("MEMORY:\n" + mem.stdout.strip())
        # Disk
        disk = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
        result.append("DISK:\n" + disk.stdout.strip())
        # Uptime
        up = subprocess.run(['uptime', '-p'], capture_output=True, text=True)
        result.append("UPTIME: " + up.stdout.strip())
        # CPU info
        cpu = subprocess.run(['nproc'], capture_output=True, text=True)
        result.append(f"CPU CORES: {cpu.stdout.strip()}")
        return '\n\n'.join(result)
    except Exception as e:
        return f"Error getting system info: {e}"

def open_app(app):
    app_map = {
        'notepad': 'notepad.exe',
        'explorer': 'explorer.exe',
        'spotify': 'spotify.exe',
        'vscode': 'code',
        'chrome': 'chrome.exe',
        'discord': 'discord.exe',
        'terminal': 'wt.exe',
        'calculator': 'calc.exe',
        'paint': 'mspaint.exe',
    }
    app_lower = app.lower().strip()
    exe = app_map.get(app_lower, app)
    try:
        subprocess.run(['cmd.exe', '/c', 'start', exe])
        return f"Opened {app}"
    except Exception as e:
        return f"Error opening {app}: {e}"

# ─── Web Tools ────────────────────────────────────────────────────────────────

def web_search(query):
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    subprocess.run(['cmd.exe', '/c', 'start', url])
    return f"Opened Google search for: {query}"

def get_weather():
    try:
        response = http_requests.get(
            "https://wttr.in/Melbourne?format=3",
            timeout=5,
            headers={'User-Agent': 'DeathAI-Reverie/1.0'}
        )
        if response.status_code == 200:
            return f"Melbourne weather: {response.text.strip()}"
        return "Could not fetch weather right now"
    except Exception as e:
        return f"Weather unavailable: {e}"

# ─── Music ────────────────────────────────────────────────────────────────────

def play_music(path):
    path_win = path.replace('/home/death', r'\\wsl$\Ubuntu\home\death')
    subprocess.run(['cmd.exe', '/c', 'start', '', path_win])
    return f"Playing {path}"

# ─── Notes & Reminders ────────────────────────────────────────────────────────

NOTES_FILE = os.path.expanduser('~/deathai/data/notes.md')
REMINDERS_FILE = os.path.expanduser('~/deathai/data/reminders.json')

def save_note(note):
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"\n## {timestamp}\n{note}\n"
        os.makedirs(os.path.dirname(NOTES_FILE), exist_ok=True)
        with open(NOTES_FILE, 'a') as f:
            f.write(entry)
        return f"Note saved: {note[:80]}{'...' if len(note) > 80 else ''}"
    except Exception as e:
        return f"Error saving note: {e}"

def read_notes():
    try:
        if not os.path.exists(NOTES_FILE):
            return "No notes yet. Start saving some!"
        with open(NOTES_FILE, 'r') as f:
            content = f.read()
        if len(content) > 3000:
            return content[-3000:]  # Most recent notes
        return content if content.strip() else "Notes file is empty."
    except Exception as e:
        return f"Error reading notes: {e}"

def set_reminder(message, minutes=5):
    try:
        minutes = int(minutes)
        remind_at = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
        reminders = []
        if os.path.exists(REMINDERS_FILE):
            with open(REMINDERS_FILE, 'r') as f:
                reminders = json.load(f)
        reminders.append({
            "message": message,
            "at": remind_at.isoformat(),
            "done": False
        })
        os.makedirs(os.path.dirname(REMINDERS_FILE), exist_ok=True)
        with open(REMINDERS_FILE, 'w') as f:
            json.dump(reminders, f, indent=2)
        return f"Reminder set: '{message}' in {minutes} minutes (at {remind_at.strftime('%H:%M')})"
    except Exception as e:
        return f"Error setting reminder: {e}"

def read_progress():
    progress_file = os.path.expanduser('~/deathai/PROGRESS.md')
    try:
        if not os.path.exists(progress_file):
            return "No progress file found yet."
        with open(progress_file, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading progress: {e}"

# ─── Tool Registry ────────────────────────────────────────────────────────────

TOOLS = {
    'open_url': open_url,
    'list_files': list_files,
    'read_file': read_file,
    'write_file': write_file,
    'create_folder': create_folder,
    'delete_file': delete_file,
    'find_files': find_files,
    'run_command': run_safe_command,
    'web_search': web_search,
    'get_weather': get_weather,
    'system_info': system_info,
    'set_reminder': set_reminder,
    'read_notes': read_notes,
    'save_note': save_note,
    'read_progress': read_progress,
    'open_app': open_app,
    'play_music': play_music,
}
