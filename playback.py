
import os
import glob
import shlex
import subprocess
import tempfile
import psutil

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
    pass
