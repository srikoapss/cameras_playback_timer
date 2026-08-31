import os, sys, json

if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULTS = {
    "APP_PATH": "C:\\Program Files\\PostgreSQL\\18\\pgAdmin 4\\runtime\\pgAdmin4.exe",
    "APP_WINDOW_TITLE": "pgAdmin 4",
    "START_HOUR": 14,
    "END_HOUR": 9,
    "START_MINUTE": 0,
    "END_MINUTE": 15,
    "APP_PROCESS_NAME": "pgAdmin4.exe",
    "FULLSCREEN_IMAGE": "fullscreen_btn.png",
    "MAIN_VIEW_IMAGE": "main_view.png",
    "STARTUP_TIMEOUT_SECONDS": 30,
    "WINDOW_CHECK_INTERVAL_SECONDS": 1,
    "FULLSCREEN_TIMEOUT_SECONDS": 120,
    "FULLSCREEN_CLICK_DELAY_SECONDS": 4,
    "PLAYBACK_VIDEO_DIR": "C:\\Videos",
    "PLAYBACK_VIDEO_PATTERN": "*.mp4",
    "PLAYBACK_PLAYER_PATH": "C:\\Program Files\\VideoLAN\\VLC\\vlc.exe",
    "PLAYBACK_PLAYER_ARGS": "--fullscreen --loop --no-video-title",
    "PLAYBACK_PROCESS_NAME": "vlc.exe",
    "PLAYBACK_TIMEOUT_SECONDS": 120
}

CONFIG_PATH = os.path.join(APP_DIR, "config.json")

def load_settings():
    # First run on a new machine: write the defaults out so there is something
    # readable for a technician to edit, then we are done.
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULTS, f, indent=4)
        return DEFAULTS

    # encoding is explicit because Windows would otherwise pick cp1252 and
    # mangle accented characters in paths.
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            loaded = json.load(f)
    except json.JSONDecodeError:
        # Hand-edited file with a syntax error: keep running on defaults
        # instead of dying at startup on the production line.
        return DEFAULTS

    # Merge left to right, so config.json wins where it defines a key and the
    # default survives where it does not. Only works because the dict is flat.
    return {**DEFAULTS, **loaded}

SETTINGS = load_settings()

def resolve_path(value):
    if os.path.isabs(value):
        return value
    return os.path.join(APP_DIR, value)

def main():
    """Install-time self-check: run `python config.py` to verify resolved paths."""
    print(f"APP_DIR     : {APP_DIR}")
    print(f"CONFIG_PATH : {CONFIG_PATH} (exists: {os.path.exists(CONFIG_PATH)})")
    print("SETTINGS    :")
    for key, value in SETTINGS.items():
        origin = "default" if key not in _loaded_keys() else "config.json"
        # :<24 pads to 24 chars; !r shows repr() so strings keep their quotes
        # and a stray space in a path is visible.
        print(f"    {key:<24} = {value!r:<48} [{origin}]")


def _loaded_keys():
    """Which keys config.json actually sets -- for the [origin] tag only."""
    if not os.path.exists(CONFIG_PATH):
        return set()
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return set(json.load(f).keys())
    except json.JSONDecodeError:
        return set()


APP_VERSION = "1.0"

if __name__ == "__main__":
    main()
