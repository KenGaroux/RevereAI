import subprocess
import os

APPROVED_COMMANDS = ['ls', 'pwd', 'mkdir', 'cat', 'echo', 'date', 'whoami', 'find']

TOOL_DEFINITIONS = """
You have access to the following tools. When you want to use a tool, respond with ONLY this JSON format on its own line:
TOOL_CALL: {"tool": "tool_name", "params": {"param_name": "value"}}

Available tools:
- open_url: Opens a URL in the browser. params: {"url": "https://..."}
- list_files: Lists files in a directory. params: {"path": "~/some/path"}
- read_file: Reads a file's contents. params: {"path": "~/some/file.txt"}
- create_folder: Creates a new folder. params: {"path": "~/new/folder"}
- run_command: Runs a safe terminal command. params: {"command": "ls -la"}
- web_search: Searches the web. params: {"query": "search terms"}

Only use a tool when the user is clearly asking you to do something on their computer.
After the tool runs, you will receive the result and should respond naturally.
If no tool is needed, just respond normally.
"""

def open_url(url):
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    subprocess.run(['cmd.exe', '/c', 'start', url])
    return f"Opened {url} in your browser"

def list_files(path='.'):
    path = os.path.expanduser(path)
    try:
        files = os.listdir(path)
        return '\n'.join(sorted(files))
    except Exception as e:
        return f"Error: {e}"

def read_file(path):
    path = os.path.expanduser(path)
    try:
        with open(path, 'r') as f:
            return f.read()[:2000]
    except Exception as e:
        return f"Error: {e}"

def create_folder(path):
    path = os.path.expanduser(path)
    try:
        os.makedirs(path, exist_ok=True)
        return f"Created folder: {path}"
    except Exception as e:
        return f"Error: {e}"

def run_safe_command(command):
    parts = command.strip().split()
    if not parts or parts[0] not in APPROVED_COMMANDS:
        return f"Command '{parts[0] if parts else ''}' not in approved list: {APPROVED_COMMANDS}"
    try:
        result = subprocess.run(parts, capture_output=True, text=True, timeout=10)
        return result.stdout or result.stderr or "Command completed"
    except Exception as e:
        return f"Error: {e}"

def web_search(query):
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    subprocess.run(['cmd.exe', '/c', 'start', url])
    return f"Opened Google search for: {query}"

def play_music(path):
    path_win = path.replace('/home/death', r'\\wsl$\Ubuntu\home\death')
    subprocess.run(['cmd.exe', '/c', 'start', '', path_win])
    return f"Playing {path}"

TOOLS = {
    'open_url': open_url,
    'list_files': list_files,
    'read_file': read_file,
    'create_folder': create_folder,
    'run_command': run_safe_command,
    'web_search': web_search,
    'play_music': play_music,
}
