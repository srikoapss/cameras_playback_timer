import subprocess
import time
from datetime import datetime

import psutil
import pyautogui
import pywinctl as pwc


class LiveApp:
    def __init__(
        self,
        app_path,
        window_title,
        process_name,
        main_view_image,
        fullscreen_image,
        startup_timeout,
        window_check_interval,
        fullscreen_timeout,
        fullscreen_click_delay,
    ):
        self.app_path = app_path
        self.window_title = window_title
        self.process_name = process_name
        self.main_view_image = main_view_image
        self.fullscreen_image = fullscreen_image
        self.startup_timeout = startup_timeout
        self.window_check_interval = window_check_interval
        self.fullscreen_timeout = fullscreen_timeout
        self.fullscreen_click_delay = fullscreen_click_delay

        # How long to keep iVMS loading behind VLC before attempting the visible handoff.
        self.warmup_seconds = 120
        # How long to wait between handoff attempts when iVMS is not ready yet.
        self.retry_seconds = 30
    
    def is_running(self):
        for proc in psutil.process_iter(["name"]):
            try:
                if proc.info["name"] == self.process_name:
                    print(f"Found running instance: {self.process_name}")
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return False

    def _find_image(self, image_path, label):
        print(f"Waiting up to {self.fullscreen_timeout} seconds for {label}...")
        deadline = time.monotonic() + self.fullscreen_timeout
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


    def refocus(self):
        windows = pwc.getWindowsWithTitle(self.window_title)

        if not windows:
            return False

        try:
            windows[0].activate()
            return True
        except Exception:
            return False

    
    def stop(self):
        """ kill the live NVR"""
        if not self.is_running():
            return

        print(f"Closing {self.process_name} at {datetime.now()}")

        subprocess.run(
            ["taskkill", "/f", "/im", self.process_name],
            capture_output=True, text=True
        )
        print(f"Closed app at {datetime.now()}")

    
    def _make_window_fullscreen(self):
        """
        Find a window by title and make it fullscreen.
        Returns True if successful, False otherwise.
        """
        print(f"Looking for window with title containing: '{self.window_title}'")
        
        # Get all windows with matching title
        deadline = time.monotonic() + self.startup_timeout
        windows = []
        while time.monotonic() < deadline:
            windows = pwc.getWindowsWithTitle(self.window_title)
            if windows:
                break
            print(f"Window not ready; checking again in {self.window_check_interval} second(s)...")
            time.sleep(self.window_check_interval)
        
        if not windows:
            print(f"No windows found with title containing '{self.window_title}'")
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
                main_view_location = self._find_image(self.main_view_image, "Main View tab")
                if not main_view_location:
                    return False
                pyautogui.click(int(main_view_location.x), int(main_view_location.y))
                print("Clicked Main View tab")

                button_location = self._find_image(self.fullscreen_image, "fullscreen button")
                if not button_location:
                    return False

                # Leave the UI untouched so temporary notifications can disappear naturally.
                print(f"Fullscreen button ready; waiting {self.fullscreen_click_delay} seconds before clicking...")
                time.sleep(self.fullscreen_click_delay)

                # Re-detect instead of using coordinates captured before the quiet period.
                button_location = self._find_image(self.fullscreen_image, "fullscreen button after quiet period")
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

    def start(self):
        if self.is_running():
            print("Live app already running")
            return True

        print(f"Launching {self.app_path} at {datetime.now()}")
        subprocess.Popen([self.app_path])
        print("Waiting for application to start...")

        success = self._make_window_fullscreen()

        if success:
            print("Window is now fullscreen")
        else:
            print("Could not make window fullscreen")

        return success

    def launch(self):
        """Start the live app process without activating or fullscreening it."""
        if self.is_running():
            print("Live app already running")
            return True

        print(f"Launching {self.app_path} at {datetime.now()}")
        try:
            subprocess.Popen([self.app_path])
            return True
        except Exception as e:
            print(f"Failed to launch live app: {e}")
            return False

    def is_window_present(self):
        return bool(pwc.getWindowsWithTitle(self.window_title))

    def wait_for_window(self, timeout=None):
        timeout = timeout if timeout is not None else self.startup_timeout
        print(f"Waiting up to {timeout} seconds for live window...")
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            if self.is_window_present():
                return True
            time.sleep(self.window_check_interval)

        print("Live window not found")
        return False

    def show_fullscreen(self):
        """Activate an existing live window and click fullscreen controls."""
        return self._make_window_fullscreen()
