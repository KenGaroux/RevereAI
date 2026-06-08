import subprocess
import os
import webbrowser

APPROVED_COMMANDS = ['ls', 'pwd', 'mkdir', 'cat', 'echo', 'date', 'whoami']

def open_url(url):
    """Open a URL in the Windows browser"""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    subprocess.run(['cmd.exe', '/c', 'start', url])
    return f"Opened {url} in your browser"

def list_files(path='.'):
    """List files in a directory"""
    path = os.path.expanduser(path)
    try:
        files = os.listdir(path)
        return '\n'.join(files)
    except Exception as e:
        return f"Error: {e}"

def read_file(path):
    """Read a file"""
    path = os.path.expanduser(path)
    try:
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error: {e}"

def create_folder(path):
    """Create a folder"""
    path = os.path.expanduser(path)
    try:
        os.makedirs(path, exist_ok=True)
        return f"Created folder: {path}"
    except Exception as e:
        return f"Error: {e}"

def run_safe_command(command):
    """Run a pre-approved safe command"""
    parts = command.strip().split()
    if not parts or parts[0] not in APPROVED_COMMANDS:
        return f"Command '{parts[0] if parts else ''}' not in approved list"
    try:
        result = subprocess.run(parts, capture_output=True, text=True, timeout=10)
        return result.stdout or result.stderr
    except Exception as e:
        return f"Error: {e}"

def play_music(path):
    """Play a music file on Windows"""
    path_win = path.replace('/home/death', r'\\wsl$\Ubuntu\home\death')
    subprocess.run(['cmd.exe', '/c', 'start', '', path_win])
    return f"Playing {path}"

TOOLS = {
    'open_url': {
        'function': open_url,
        'description': 'Open a URL in the browser',
        'params': ['url']
    },
    'list_files': {
        'function': list_files,
        'description': 'List files in a directory',
        'params': ['path']
    },
    'read_file': {
        'function': read_file,
        'description': 'Read contents of a file',
        'params': ['path']
    },
    'create_folder': {
        'function': create_folder,
        'description': 'Create a new folder',
        'params': ['path']
    },
    'run_command': {
        'function': run_safe_command,
        'description': 'Run a safe terminal command',
        'params': ['command']
    },
    'play_music': {
        'function': play_music,
        'description': 'Play a music file',
        'params': ['path']
    }
}
