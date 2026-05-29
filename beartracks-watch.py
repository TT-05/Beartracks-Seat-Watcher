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

def bool_env(name, default=False):
    value = os.getenv(name, "").strip().lower()
    if not value:
        return default
    return value in ("1", "true", "yes", "y", "on")

# =========================

# Basic settings

# =========================

PROFILE_DIR = str(Path.home() / "beartracks_watch_chrome_profile")

REFRESH_INTERVAL = (180, 240)

AUTO_ENTER_ENROLLMENT = bool_env("AUTO_ENTER_ENROLLMENT", False)

TARGET_COURSE = (os.getenv("TARGET_COURSE", "CMPUT 328").strip() or "CMPUT 328").upper()

TARGET_TERM = os.getenv("TARGET_TERM", "Fall Term 2026").strip() or "Fall Term 2026"

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
    TARGET_TERM,
]

TARGET_COURSE_TEXTS = [
    TARGET_COURSE,
]

ENROLLMENT_PAGE_RE = re.compile(
    r"(Class Selection|Select a class option|Course Information)",
    re.IGNORECASE,
)

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

def course_code_pattern(course):
    parts = course.upper().split()
    if len(parts) >= 2:
        subject = re.escape(parts[0])
        number = re.escape(parts[1])
        return re.compile(rf"\b{subject}\s*[-\s]?\s*{number}\b", re.IGNORECASE)
    return re.compile(re.escape(course), re.IGNORECASE)

def get_target_open_seats_by_position(page):
    target_re = course_code_pattern(TARGET_COURSE)
    results = []

    for frame in page.frames:
        try:
            frame_results = frame.evaluate(
                """
                ({ targetPattern }) => {
                    const targetRe = new RegExp(targetPattern, "i");
                    const anyCourseRe = /\\b[A-Z]{2,6}\\s*[-\\s]?\\s*\\d{3}[A-Z]?\\b/i;
                    const seatRe = /Open\\s*Seats\\s*(\\d+)\\s*of\\s*(\\d+)/i;

                    function isVisible(el) {
                        const style = window.getComputedStyle(el);
                        const rect = el.getBoundingClientRect();
                        return (
                            rect.width > 0 &&
                            rect.height > 0 &&
                            style.display !== "none" &&
                            style.visibility !== "hidden" &&
                            Number(style.opacity) !== 0
                        );
                    }

                    const items = [];
                    for (const el of document.body.querySelectorAll("*")) {
                        if (!isVisible(el)) {
                            continue;
                        }

                        const text = (el.innerText || el.textContent || "").replace(/\\s+/g, " ").trim();
                        if (!text || text.length > 300) {
                            continue;
                        }

                        const rect = el.getBoundingClientRect();
                        items.push({
                            text,
                            x: rect.left,
                            y: rect.top,
                            w: rect.width,
                            h: rect.height,
                            cx: rect.left + rect.width / 2,
                            cy: rect.top + rect.height / 2,
                        });
                    }

                    const rawTargets = items
                        .filter((item) => targetRe.test(item.text))
                        .sort((a, b) => a.y - b.y || a.x - b.x);

                    const targets = [];
                    for (const target of rawTargets) {
                        const duplicate = targets.find((existing) => {
                            return (
                                Math.abs(existing.x - target.x) < 24 &&
                                Math.abs(existing.y - target.y) < 24
                            );
                        });

                        if (!duplicate) {
                            targets.push(target);
                            continue;
                        }

                        if (target.w * target.h < duplicate.w * duplicate.h) {
                            Object.assign(duplicate, target);
                        }
                    }

                    const courseHeadings = items
                        .filter((item) => anyCourseRe.test(item.text))
                        .sort((a, b) => a.y - b.y || a.x - b.x);

                    const rawSeats = items
                        .map((item) => {
                            const match = item.text.match(seatRe);
                            if (!match) {
                                return null;
                            }
                            return {
                                open: Number(match[1]),
                                total: Number(match[2]),
                                raw: match[0],
                                x: item.x,
                                y: item.y,
                                w: item.w,
                                h: item.h,
                                cy: item.cy,
                            };
                        })
                        .filter(Boolean)
                        .sort((a, b) => a.y - b.y || a.x - b.x);

                    const seats = [];
                    for (const seat of rawSeats) {
                        const duplicate = seats.find((existing) => {
                            return (
                                existing.open === seat.open &&
                                existing.total === seat.total &&
                                Math.abs(existing.x - seat.x) < 24 &&
                                Math.abs(existing.y - seat.y) < 24
                            );
                        });

                        if (!duplicate) {
                            seats.push(seat);
                            continue;
                        }

                        if (seat.w * seat.h < duplicate.w * duplicate.h) {
                            Object.assign(duplicate, seat);
                        }
                    }

                    const matched = [];
                    const seen = new Set();

                    for (const target of targets) {
                        const nextCourse = courseHeadings.find((item) => {
                            return (
                                item.y > target.y + Math.max(target.h, 20) &&
                                item.x >= target.x - 220 &&
                                item.x <= target.x + 320
                            );
                        });

                        const blockTop = target.y - 25;
                        const blockBottom = nextCourse ? nextCourse.y - 5 : target.y + 260;

                        for (const seat of seats) {
                            if (seat.x <= target.x || seat.cy < blockTop || seat.cy >= blockBottom) {
                                continue;
                            }

                            const key = `${seat.raw}:${Math.round(seat.x)}:${Math.round(seat.y)}`;
                            if (seen.has(key)) {
                                continue;
                            }

                            seen.add(key);
                            matched.push({
                                open: seat.open,
                                total: seat.total,
                                raw: seat.raw,
                            });
                        }
                    }

                    return matched;
                }
                """,
                {"targetPattern": target_re.pattern},
            )

            results.extend(frame_results)
        except Exception:
            pass

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

        if get_target_open_seats_by_position(page):

            log(f"Detected Open Seats for {TARGET_COURSE}. Current page is monitorable.")

            return

        target_seen = bool(course_code_pattern(TARGET_COURSE).search(text))
        open_seats_seen = "Open Seats" in text
        log(
            f"Could not detect Open Seats for {TARGET_COURSE} on the current page. "
            f"target_seen={target_seen}, open_seats_seen={open_seats_seen}"
        )

        print("Please confirm:")

        print("1. You are on the Bear Tracks Watch List or Cart page")

        print("2. The page is fully loaded")

        print(f"3. You can visually see {TARGET_COURSE} and Open Seats X of Y")

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

def wait_for_text(page, pattern, timeout=30000, poll_seconds=2):
    deadline = time.time() + timeout / 1000

    while time.time() < deadline:
        text = get_all_visible_text(page)
        if pattern.search(text):
            return text
        time.sleep(poll_seconds)

    return get_all_visible_text(page)

def enter_enrollment_page(page):
    notify(f"Open seat found for {TARGET_COURSE}. Trying to enter Class Search and Enroll.")

    if not click_text_in_any_frame(page, "Class Search and Enroll"):
        notify("Could not click Class Search and Enroll automatically.")
        return False

    time.sleep(random.randint(5, 8))
    text = get_all_visible_text(page)

    if "Choose a Term" in text:
        if not click_text_in_any_frame(page, TARGET_TERM_TEXTS):
            notify(f"Could not select {TARGET_TERM} automatically.")
            return False
        time.sleep(random.randint(5, 8))
        text = get_all_visible_text(page)

    if "Search For Classes" not in text and not any(course in text for course in TARGET_COURSE_TEXTS):
        text = wait_for_text(page, re.compile(
            rf"(Search For Classes|{re.escape(TARGET_COURSE)})",
            re.IGNORECASE,
        ))

    if not any(course in text for course in TARGET_COURSE_TEXTS):
        notify(f"Could not find {TARGET_COURSE} in Class Search and Enroll.")
        return False

    if not click_text_in_any_frame(page, TARGET_COURSE_TEXTS):
        notify(f"Could not open {TARGET_COURSE} automatically.")
        return False

    text = wait_for_text(page, ENROLLMENT_PAGE_RE)
    if ENROLLMENT_PAGE_RE.search(text):
        notify(f"Entered {TARGET_COURSE} enrollment page.")
        return True

    notify(f"Clicked {TARGET_COURSE}, but the enrollment page was not confirmed.")
    return False

def handle_open_seat(page):
    if not AUTO_ENTER_ENROLLMENT:
        notify("Auto-enter enrollment is disabled. Please enroll manually.")
        return False

    if not enter_enrollment_page(page):
        return False

    notify("The enrollment page is open for manual review.")
    input("Press Enter after you finish or want the watcher to continue: ")
    return False

def return_to_watchlist_page(page):
    log("Trying to return to Watch List page...")

    time.sleep(random.randint(5, 8))

    if not click_text_in_any_frame(page, TARGET_MENU_TEXTS):
        notify("Could not click Shopping Cart and Watch List. Please return manually.")
        return False

    time.sleep(random.randint(5, 8))

    if not click_text_in_any_frame(page, TARGET_TERM_TEXTS):
        notify(f"Could not click {TARGET_TERM}. Please select the term manually.")
        return False

    time.sleep(random.randint(8, 12))

    text = get_all_visible_text(page)
    if get_target_open_seats_by_position(page):
        log("Returned to Watch List page successfully.")
        return True

    log(f"Clicked target page, but Open Seats for {TARGET_COURSE} was not detected yet.")
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

                seats = get_target_open_seats_by_position(page)

                if not seats:

                    log(f"No Open Seats information found for {TARGET_COURSE}. The page may still be loading or may not be a target page.")

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

                            lines = [f"Bear Tracks open seat detected for {TARGET_COURSE}:"]

                            for idx, open_seats, total_seats in open_items:

                                lines.append(f"Item {idx}: Open Seats {open_seats} of {total_seats}")

                            lines.append("Please open Bear Tracks and enroll manually.")

                            notify("\n".join(lines))

                            last_alert_state = alert_state

                            if handle_open_seat(page):
                                notify("Auto-enrollment completed. Stopping watcher.")
                                context.close()
                                break

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
