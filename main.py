import time
from datetime import datetime, time as dt_time

import playback
from config import SETTINGS, resolve_path
from live_app import LiveApp


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

live_app = LiveApp(
    app_path=APP_PATH,
    window_title=APP_WINDOW_TITLE,
    process_name=APP_PROCESS_NAME,
    main_view_image=MAIN_VIEW_IMAGE,
    fullscreen_image=FULLSCREEN_IMAGE,
    startup_timeout=STARTUP_TIMEOUT_SECONDS,
    window_check_interval=WINDOW_CHECK_INTERVAL_SECONDS,
    fullscreen_timeout=FULLSCREEN_TIMEOUT_SECONDS,
    fullscreen_click_delay=FULLSCREEN_CLICK_DELAY_SECONDS,
)


def current_mode(now):
    start = dt_time(START_HOUR, START_MINUTE)
    end = dt_time(END_HOUR, END_MINUTE)
    now_time = now.time()

    if start < end :
        return "live" if start <= now_time < end else "playback"
    else:
         # Live window wraps around midnight, e.g., 22:00 to 06:00
        return "live" if now_time >= start or now_time < end else "playback"

def main():
    try:
        live_fullscreen = False

        while True:
            now = datetime.now()
            mode = current_mode(now)
            print(f"Mode : {mode} at {now}")

            if mode == "live":
                # It's time to go live.
                if not live_app.is_running():
                    live_fullscreen = False
                    if not live_app.launch():
                        print("Live launch failed; retrying...")
                        time.sleep(live_app.retry_seconds)
                        continue

                    print("iVMS launched; keeping VLC visible while it loads")

                if not live_fullscreen:
                    # Keep VLC visible while iVMS loads in the background.
                    if live_app.is_window_present():
                        print(f"iVMS window detected; warming up for {live_app.warmup_seconds} seconds...")
                        time.sleep(live_app.warmup_seconds)

                        if live_app.show_fullscreen():
                            print("iVMS is fullscreen; stopping VLC")
                            playback.stop_playback()
                            live_fullscreen = True
                        else:
                            print("iVMS fullscreen failed; returning focus to VLC")
                            playback.refocus_playback()
                    else:
                        print("iVMS window not ready yet; keeping VLC in front")
                        playback.refocus_playback()

                    time.sleep(live_app.retry_seconds)
                    continue

                while current_mode(datetime.now()) == "live":
                    live_app.refocus()
                    time.sleep(60)

            else:
                # It's time to go playback.
                live_fullscreen = False
                live_app.stop()

                if not playback.is_playback_running():
                    process = playback.start_playback()

                    if not process:
                        print("Playback setup failed; retrying in 60 seconds")
                        time.sleep(60)
                        continue

                while current_mode(datetime.now()) == "playback":
                    playback.refocus_playback()
                    time.sleep(60)

    except KeyboardInterrupt:
        print("Script stopped by user")
        playback.stop_playback()
        live_app.stop()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()