import os
import subprocess
import webbrowser
import urllib.parse
import ctypes
import datetime

# Virtual Key Codes for Media and System
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_MEDIA_PLAY_PAUSE = 0xB3

def launch_application(app_name: str) -> str:
    """
    Launches an application or program on Windows.
    Examples: 'chrome', 'notepad', 'calculator', 'vs code', 'spotify', 'explorer', 'terminal'.
    """
    app_lower = app_name.lower().strip()
    
    app_map = {
        'chrome': 'chrome',
        'google chrome': 'chrome',
        'notepad': 'notepad',
        'calculator': 'calc',
        'calc': 'calc',
        'vscode': 'code',
        'vs code': 'code',
        'code': 'code',
        'spotify': 'spotify',
        'explorer': 'explorer',
        'file explorer': 'explorer',
        'cmd': 'cmd',
        'terminal': 'wt',
        'task manager': 'taskmgr',
        'paint': 'mspaint',
        'settings': 'start ms-settings:',
        'edge': 'msedge'
    }
    
    target = app_map.get(app_lower, app_lower)
    try:
        if target.startswith('start '):
            os.system(target)
        else:
            subprocess.Popen(target, shell=True)
        return f"Successfully opened {app_name}."
    except Exception as e:
        return f"Could not launch {app_name}: {e}"

def open_website(url: str) -> str:
    """
    Opens a website in the default browser.
    """
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'https://' + url
    try:
        webbrowser.open(url)
        return f"Opened website: {url}"
    except Exception as e:
        return f"Failed to open website {url}: {e}"

def search_web(query: str) -> str:
    """
    Searches Google for the given search query.
    """
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    webbrowser.open(url)
    return f"Searched Google for: {query}"

def play_youtube(query: str) -> str:
    """
    Searches and plays a video on YouTube for the given query.
    """
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
    webbrowser.open(url)
    return f"Opened YouTube search for: {query}"

def control_volume(action: str) -> str:
    """
    Adjusts system volume: 'up', 'down', or 'mute'.
    """
    action = action.lower().strip()
    user32 = ctypes.windll.user32
    
    if action == 'up':
        for _ in range(5):
            user32.keybd_event(VK_VOLUME_UP, 0, 0, 0)
            user32.keybd_event(VK_VOLUME_UP, 0, 2, 0)
        return "Volume increased."
    elif action == 'down':
        for _ in range(5):
            user32.keybd_event(VK_VOLUME_DOWN, 0, 0, 0)
            user32.keybd_event(VK_VOLUME_DOWN, 0, 2, 0)
        return "Volume decreased."
    elif action == 'mute':
        user32.keybd_event(VK_VOLUME_MUTE, 0, 0, 0)
        user32.keybd_event(VK_VOLUME_MUTE, 0, 2, 0)
        return "Volume muted/unmuted."
    elif action in ['play', 'pause', 'play_pause']:
        user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
        user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 2, 0)
        return "Toggled media play/pause."
    return f"Unknown volume action: {action}"

def lock_workstation() -> str:
    """
    Locks the Windows computer.
    """
    ctypes.windll.user32.LockWorkStation()
    return "Workstation locked."

def get_current_time_date() -> str:
    """
    Gets the current date and time.
    """
    now = datetime.datetime.now()
    return f"Current time is {now.strftime('%I:%M %p')} on {now.strftime('%A, %B %d, %Y')}."
