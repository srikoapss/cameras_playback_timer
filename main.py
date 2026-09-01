import subprocess
import time
import pyautogui
import pywinctl as pwc
from datetime import datetime
from config import SETTINGS, resolve_path    
import psutil
import subprocess
from datetime import datetime, time as dt_time
import playback


# Configuration
APP_PATH = SETTINGS["APP_PATH"]
APP_WINDOW_TITLE = SETTINGS["APP_WINDOW_TITLE"]  # Exact title that appears in window title bar
START_HOUR = SETTINGS["START_HOUR"]  
END_HOUR = SETTINGS["END_HOUR"]    
START_MINUTE = SETTINGS["START_MINUTE"]
END_MINUTE = SETTINGS["END_MINUTE"]
APP_PROCESS_NAME = SETTINGS["APP_PROCESS_NAME"] # The actual process name to kill
FULLSCREEN_IMAGE = resolve_path(SETTINGS["FULLSCREEN_IMAGE"])
MAIN_VIEW_IMAGE = resolve_path(SETTINGS["MAIN_VIEW_IMAGE"])
STARTUP_TIMEOUT_SECONDS = SETTINGS["STARTUP_TIMEOUT_SECONDS"]
WINDOW_CHECK_INTERVAL_SECONDS = SETTINGS["WINDOW_CHECK_INTERVAL_SECONDS"]
FULLSCREEN_TIMEOUT_SECONDS = SETTINGS["FULLSCREEN_TIMEOUT_SECONDS"]
FULLSCREEN_CLICK_DELAY_SECONDS = SETTINGS["FULLSCREEN_CLICK_DELAY_SECONDS"]
PLAYBACK_VIDEO_DIR = resolve_path(SETTINGS["PLAYBACK_VIDEO_DIR"])
PLAYBACK_VIDEO_PATTERN = SETTINGS["PLAYBACK_VIDEO_PATTERN"]
PLAYBACK_PLAYER_PATH = resolve_path(SETTINGS["PLAYBACK_PLAYER_PATH"])
PLAYBACK_PLAYER_ARGS = SETTINGS["PLAYBACK_PLAYER_ARGS"]
PLAYBACK_PROCESS_NAME = SETTINGS["PLAYBACK_PROCESS_NAME"]
PLAYBACK_TIMEOUT_SECONDS = SETTINGS["PLAYBACK_TIMEOUT_SECONDS"]

def find_image(image_path, label):
    print(f"Waiting up to {FULLSCREEN_TIMEOUT_SECONDS} seconds for {label}...")
    deadline = time.monotonic() + FULLSCREEN_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        try:
            location = pyautogui.locateCenterOnScreen(image_path, confidence=0.8)
        except pyautogui.ImageNotFoundException:
            location = None
        if location:
            print(f"Found {label}: {location}")
            return location
        time.sleep(1)
    print(f"Failed finding {label}")
    return None
    



def is_app_running():
    """Check if the app process is already running."""
    process_name = APP_PROCESS_NAME
    
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] == process_name:
                print(f"Found running instance: {process_name}")
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

def make_window_fullscreen(window_title, timeout=STARTUP_TIMEOUT_SECONDS):
    """
    Find a window by title and make it fullscreen.
    Returns True if successful, False otherwise.
    """
    print(f"Looking for window with title containing: '{window_title}'")
    
    # Get all windows with matching title
    deadline = time.monotonic() + timeout
    windows = []
    while time.monotonic() < deadline:
        windows = pwc.getWindowsWithTitle(window_title)
        if windows:
            break
        print(f"Window not ready; checking again in {WINDOW_CHECK_INTERVAL_SECONDS} second(s)...")
        time.sleep(WINDOW_CHECK_INTERVAL_SECONDS)
    
    if not windows:
        print(f"No windows found with title containing '{window_title}'")
        # Show available windows for debugging
        print("Available windows:")
        for w in pwc.getAllWindows():
            if w.title:
                print(f"  - {w.title}")
        return False
    
    # Try each matching window (in case there are multiple)
    for i, win in enumerate(windows):
        print(f"Found window {i+1}: '{win.title}'")
        
        try:
            # Step 1: Bring window to foreground
            print(f"Activating window: '{win.title}'")
            win.activate()
            time.sleep(0.5)  # Give time for window to gain focus
            
            # Step 2: Verify this is the active window
            active_window = pwc.getActiveWindow()
            if active_window and active_window.title == win.title:
                print("Window is now active and focused")
            else:
                print("Warning: Window may not be active, but trying anyway")
            
            # Method 1: Try Fn + F11
            main_view_location = find_image(MAIN_VIEW_IMAGE, "Main View tab")
            if not main_view_location:
                return False
            pyautogui.click(int(main_view_location.x), int(main_view_location.y))
            print("Clicked Main View tab")

            button_location = find_image(FULLSCREEN_IMAGE, "fullscreen button")
            if not button_location:
                return False

            # Leave the UI untouched so temporary notifications can disappear naturally.
            print(f"Fullscreen button ready; waiting {FULLSCREEN_CLICK_DELAY_SECONDS} seconds before clicking...")
            time.sleep(FULLSCREEN_CLICK_DELAY_SECONDS)

            # Re-detect instead of using coordinates captured before the quiet period.
            button_location = find_image(FULLSCREEN_IMAGE, "fullscreen button after quiet period")
            if not button_location:
                return False
            pyautogui.click(int(button_location.x), int(button_location.y))
            time.sleep(0.5)
            print("Clicked fullscreen button")
            return True
            
        except Exception as e:
            print(f"Error with window {i+1}: {e}")
            continue
    
    return False

def refocus_window(title):
    """Bring the first matching window to the foreground."""
    windows = pwc.getWindowsWithTitle(title)

    if windows:
        try:
            windows[0].activate()
        except Exception:
            pass


def current_mode(now):
    start = dt_time(START_HOUR, START_MINUTE)
    end = dt_time(END_HOUR, END_MINUTE)
    now_time = now.time()

    if start < end :
        return "live" if start <= now_time < end else "playback"
    else:
         # Live window wraps around midnight, e.g., 22:00 to 06:00
        return "live" if now_time >= start or now_time < end else "playback"

def run_live():

    if is_app_running():
        print("Live app already running")
        return True
    
    print(f"Launching {APP_PATH} at {datetime.now()}")
    subprocess.Popen([APP_PATH])
    print("Waiting for application to start...")

    success = make_window_fullscreen(APP_WINDOW_TITLE)

    if success:
        print("Window is now fullscreen")
    else:
        print("Could not make window fullscreen")
    
    return success

def stop_live():
    """ kill the live NVR"""
    print(f"Closing {APP_PROCESS_NAME} at {datetime.now()}")

    subprocess.run(
        ["taskkill", "/f", "/im", APP_PROCESS_NAME],
        capture_output=True, text=True
    )
    print(f"Closed app at {datetime.now()}")


def main():
    try:
        keep_runing = True
        while keep_runing:
            now = datetime.now()
            mode = current_mode(now)
            print(f"Mode : {mode} at {now}")

            if mode == "live":
                # its time to go live mode 
                playback.stop_playback()

                if not is_app_running():
                    if not run_live():
                        print("Live setup failed; retrying in 60 seconds")
                        time.sleep(60)
                        continue
                   
                while current_mode(datetime.now()) == "live":
                    refocus_window(APP_WINDOW_TITLE)
                    time.sleep(60)
            
            else:
                #its time to go playback mode 
                stop_live()

                if not playback.is_playback_running():
                    process = playback.start_playback()

                    if not process:
                        print("Playback setup failed; retrying in 60 seconds")
                        time.sleep(60)
                        continue
                
                while current_mode(datetime.now()) == "playback":
                    refocus_window("VLC media player")
                    time.sleep(60)
                

        
    except KeyboardInterrupt:
        print("Script stopped by user")
        playback.stop_playback()
        stop_live()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()