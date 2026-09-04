
import os
import glob
import shlex
import subprocess
import tempfile
import psutil
import pywinctl as pwc

from config import resolve_path, SETTINGS

PLAYBACK_VIDEO_DIR = resolve_path(SETTINGS["PLAYBACK_VIDEO_DIR"])
PLAYBACK_VIDEO_PATTERN = SETTINGS["PLAYBACK_VIDEO_PATTERN"]
PLAYBACK_PLAYER_PATH = resolve_path(SETTINGS["PLAYBACK_PLAYER_PATH"])
PLAYBACK_PLAYER_ARGS = SETTINGS["PLAYBACK_PLAYER_ARGS"]
PLAYBACK_PROCESS_NAME = SETTINGS["PLAYBACK_PROCESS_NAME"]
PLAYBACK_TIMEOUT_SECONDS = SETTINGS["PLAYBACK_TIMEOUT_SECONDS"]

def get_video_files():
    search_pattern = os.path.join(PLAYBACK_VIDEO_DIR,PLAYBACK_VIDEO_PATTERN)
    files_list = glob.glob(search_pattern)
    final_list = []

    for file in files_list:
        if os.path.isfile(file):
            final_list.append(file)
    
    final_list.sort(key=os.path.getmtime, reverse=True)
            
    return final_list

def build_playlist(video_files):
    
    with tempfile.NamedTemporaryFile(
            mode='w', suffix='.m3u', delete=False, encoding='utf-8'
        ) as temp_file:
            temp_file.write("#EXTM3U\n")
            for video in video_files:
                temp_file.write(video + '\n')
    
    return temp_file.name

def start_playback():
    playback_videos = get_video_files()
    if not playback_videos:
        print(f'No playback videos found')
        return None
    
    # Check if the player executable exists
    if not os.path.exists(PLAYBACK_PLAYER_PATH):
        print(f'Player not found at: {PLAYBACK_PLAYER_PATH}')
        return None
    
    playlist_path = build_playlist(playback_videos)
    cmd = [PLAYBACK_PLAYER_PATH] + shlex.split(PLAYBACK_PLAYER_ARGS) + [playlist_path]
    
    try:
        sub_process = subprocess.Popen(cmd)
        return sub_process
    except Exception as e:
        print(f'Failed to start playback: {e}')
        return None

def stop_playback():

    try:
        # Use shell=True because we're using a Windows shell command
        print(f"Stopping {PLAYBACK_PROCESS_NAME}")
        subprocess.run(
            ["taskkill", "/f", "/im", PLAYBACK_PROCESS_NAME],
            capture_output=True,
            text=True
        )
    except Exception as e:
        print(f"Error stopping playback: {e}")

def refocus_playback():
    windows = pwc.getWindowsWithTitle("VLC media player")

    if not windows:
        return False

    try:
        windows[0].activate()
        return True
    except Exception:
        return False

def is_playback_running():
    process_name = PLAYBACK_PROCESS_NAME

    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] == process_name:
                print(f'found running playback')
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return False
