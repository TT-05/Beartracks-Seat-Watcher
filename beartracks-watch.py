import os

import re

import time

import random

from pathlib import Path

from datetime import datetime

import requests

from dotenv import load_dotenv

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

load_dotenv()

# =========================

# Telegram configuration

# =========================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# =========================

# Basic settings

# =========================

PROFILE_DIR = str(Path.home() / "beartracks_watch_chrome_profile")

REFRESH_INTERVAL = (180, 240)

SEAT_RE = re.compile(r"Open Seats\s+(\d+)\s+of\s+(\d+)", re.IGNORECASE)

LOGIN_RE = re.compile(

    r"(ccid|sign\s*in|log\s*in|password|single\s*sign[- ]?on|multi[- ]?factor|mfa)",

    re.IGNORECASE,

)

TARGET_MENU_TEXTS = [
    "Shopping Cart and Watch List",
    "Shopping Cart and Watchlist",
    "Shopping Cart",
]

TARGET_TERM_TEXTS = [
    "Fall Term 2026",
]

def now():

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log(message):

    print(f"[{now()}] {message}", flush=True)

def send_telegram(message):

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:

        log("Telegram is not configured. Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID.")

        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    try:

        response = requests.post(

            url,

            json={

                "chat_id": TELEGRAM_CHAT_ID,

                "text": message,

                "disable_web_page_preview": True,

            },

            timeout=15,

        )

        response.raise_for_status()

        return True

    except Exception as e:

        log(f"Telegram send failed: {e}")

        return False

def notify(message):

    log(message)

    send_telegram(message)

def random_wait_seconds():

    return random.randint(REFRESH_INTERVAL[0], REFRESH_INTERVAL[1])

def get_all_visible_text(page):

    """

    Read visible text from the main page and all frames/iframes.

    Bear Tracks / PeopleSoft may load real content dynamically.

    """

    texts = []

    for frame in page.frames:

        try:

            body_text = frame.locator("body").inner_text(timeout=8000)

            if body_text:

                texts.append(body_text)

        except Exception:

            pass

    return "\n".join(texts)

def is_login_page(text):

    return bool(LOGIN_RE.search(text))

def parse_open_seats(text):

    results = []

    for match in SEAT_RE.finditer(text):

        open_seats = int(match.group(1))

        total_seats = int(match.group(2))

        results.append(

            {

                "open": open_seats,

                "total": total_seats,

                "raw": match.group(0),

            }

        )

    return results

def confirm_watchlist_page(page):

    """

    Confirm that the current page can be monitored before starting the loop.

    """

    while True:

        text = get_all_visible_text(page)

        if is_login_page(text):

            notify("Bear Tracks may be on the login page. Please log in manually and go to your Watch List or Cart page.")

            input("After logging in and opening the target page, press Enter to continue: ")

            continue

        if "Open Seats" in text:

            log("Detected Open Seats. Current page is monitorable.")

            return

        log("Could not detect Open Seats on the current page.")

        print("Please confirm:")

        print("1. You are on the Bear Tracks Watch List or Cart page")

        print("2. The page is fully loaded")

        print("3. You can visually see Open Seats X of Y")

        input("After confirming, press Enter to check again: ")

def click_text_in_any_frame(page, possible_texts, timeout=8000):
    if isinstance(possible_texts, str):
        possible_texts = [possible_texts]

    for text in possible_texts:
        for frame in page.frames:
            try:
                locator = frame.get_by_text(text, exact=True).first
                locator.click(timeout=timeout)
                log(f'Clicked exact text: "{text}"')
                return True
            except Exception:
                pass

            try:
                locator = frame.get_by_text(text, exact=False).first
                locator.click(timeout=timeout)
                log(f'Clicked partial text: "{text}"')
                return True
            except Exception:
                pass

    log(f"Could not click any of these texts: {possible_texts}")
    return False

def return_to_watchlist_page(page):
    log("Trying to return to Watch List page...")

    time.sleep(random.randint(5, 8))

    if not click_text_in_any_frame(page, TARGET_MENU_TEXTS):
        notify("Could not click Shopping Cart and Watch List. Please return manually.")
        return False

    time.sleep(random.randint(5, 8))

    if not click_text_in_any_frame(page, TARGET_TERM_TEXTS):
        notify("Could not click Fall Term 2026. Please select the term manually.")
        return False

    time.sleep(random.randint(8, 12))

    text = get_all_visible_text(page)
    if "Open Seats" in text:
        log("Returned to Watch List page successfully.")
        return True

    log("Clicked target page, but Open Seats was not detected yet.")
    return False

def main():

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:

        print()

        print("Telegram is not configured.")

        print("Run:")

        print("python setup_telegram.py")

        print()

        return

    notify("Bear Tracks Seat Watcher started. Please log in manually and open your Watch List or Cart page.")

    last_alert_state = None

    with sync_playwright() as p:

        context = p.chromium.launch_persistent_context(

            user_data_dir=PROFILE_DIR,

            channel="chrome",

            headless=False,

            viewport={"width": 1400, "height": 900},

            slow_mo=100,

            args=[

                "--disable-blink-features=AutomationControlled",

            ],

        )

        page = context.pages[0] if context.pages else context.new_page()

        page.goto(

            "https://www.beartracks.ualberta.ca",

            wait_until="domcontentloaded",

            timeout=60000,

        )

        print()

        print("In the opened Chrome window:")

        print("1. Log in to Bear Tracks manually")

        print("2. Go to your Watch List or Cart page")

        print("3. Make sure the page shows Open Seats X of Y")

        input("When ready, press Enter to start page detection: ")

        confirm_watchlist_page(page)

        notify("Started monitoring Bear Tracks.")

        while True:

            try:

                text = get_all_visible_text(page)

                if is_login_page(text):

                    notify("Bear Tracks may have logged out. Please log in manually again and return to the target page.")

                    input("After logging in and returning to the target page, press Enter to continue: ")

                    confirm_watchlist_page(page)

                    notify("Monitoring resumed.")

                    continue

                seats = parse_open_seats(text)

                if not seats:

                    log("No Open Seats information found. The page may still be loading or may not be a target page.")

                else:

                    open_items = []

                    for idx, item in enumerate(seats, start=1):

                        open_seats = item["open"]

                        total_seats = item["total"]

                        log(f"Item {idx}: Open Seats {open_seats} of {total_seats}")

                        if open_seats > 0:

                            open_items.append((idx, open_seats, total_seats))

                    if open_items:

                        alert_state = tuple(open_items)

                        if alert_state != last_alert_state:

                            lines = ["Bear Tracks open seat detected:"]

                            for idx, open_seats, total_seats in open_items:

                                lines.append(f"Item {idx}: Open Seats {open_seats} of {total_seats}")

                            lines.append("Please open Bear Tracks and enroll manually.")

                            notify("\n".join(lines))

                            last_alert_state = alert_state

                        else:

                            log("Open seats still exist, but the state has not changed. Telegram alert not repeated.")

                    else:

                        last_alert_state = None

                        log("No open seats currently.")

                wait_seconds = random_wait_seconds()

                log(f"Waiting {wait_seconds} seconds before refresh.")

                time.sleep(wait_seconds)

                page.reload(wait_until="domcontentloaded", timeout=60000)

                time.sleep(random.randint(8, 15))
                
                return_to_watchlist_page(page)

            except PlaywrightTimeoutError:

                notify("Bear Tracks page read or refresh timed out. The program will wait and continue.")

                time.sleep(random_wait_seconds())

                try:

                    page.reload(wait_until="domcontentloaded", timeout=60000)

                    time.sleep(random.randint(8, 15))
                    
                    return_to_watchlist_page(page)

                except Exception as e:

                    log(f"Refresh failed: {e}")

            except KeyboardInterrupt:

                notify("Bear Tracks Seat Watcher stopped manually.")

                context.close()

                break

            except Exception as e:

                notify(f"Program error, but it will continue running: {e}")

                time.sleep(random_wait_seconds())

if __name__ == "__main__":

    main()
