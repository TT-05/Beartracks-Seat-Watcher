# Bear Tracks Seat Watcher

A lightweight local Python tool for monitoring UAlberta Bear Tracks course pages for open seats.

It uses Playwright to open a real Chrome browser session, reads visible page text such as `Open Seats X of Y`, and sends Telegram alerts when seats become available or when manual re-login is needed.

## Features

- Monitors Bear Tracks Watch List or Cart pages

- Reads rendered page text, including frames and iframes

- Sends Telegram alerts to your phone

- Uses a persistent local Chrome profile

- Random refresh interval: 180–240 seconds

- Supports `.env` configuration

- Optional auto-enter enrollment page control

- Includes a Telegram setup helper

- Does not store your CCID or password

- Does not auto-enroll

- Does not bypass MFA, CAPTCHA, or login protection

## Requirements

- macOS or Windows

- Python 3

- Google Chrome

- Telegram account

- Telegram bot token

## Installation and Auto Running

If you do not have python, install via the link: 
https://www.python.org/downloads/

If you do not have git, install git via the link:
https://git-scm.com/download/win

Clone the repository:

```
git clone https://github.com/TT-05/Beartracks-Seat-Watcher.git

cd beartracks-seat-watcher

```

Run the macOS script:

```
chmod +x run.sh
./run.sh
```

On Windows, run PowerShell in the project folder:

```
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\run.ps1
```

The scripts create a virtual environment, install Python dependencies, and install Playwright Chrome support. Then, if needed, they run setup_telegram.py to help set up the Telegram bot. When everything is ready, they run beartracks-watch.py.

## Telegram Setup

Create a Telegram bot manually using `@BotFather`.

In Telegram:

1. Search `@BotFather`

2. Send `/newbot`

3. Follow the instructions

Copy the bot token and paste it when setup_telegram.py ask for it.

The helper will ask for your bot token, ask you to send `/start` or `test` to your bot, then automatically find your `chat_id` and save both values into a local `.env` file.

## Auto-Enter Enrollment Page

Auto-enter is disabled by default. Add this optional setting to `.env` only if you want the watcher to open the enrollment page after an open seat is detected:

```
AUTO_ENTER_ENROLLMENT=false
```

`run.sh` and `run.ps1` ask which term and course to monitor before starting. Use Bear Tracks term text such as `Fall Term 2026`; pressing Enter uses `Fall Term 2026`. The course answer is passed as `TARGET_COURSE`; pressing Enter uses `CMPUT 328`.

`AUTO_ENTER_ENROLLMENT=true` makes the watcher click `Class Search and Enroll`, select the target term if Bear Tracks asks for a term, open the selected target course, and stop on the course enrollment page.

Recommended first test:

```
TARGET_TERM="Fall Term 2026"
TARGET_COURSE="CMPUT 328"
AUTO_ENTER_ENROLLMENT=true
```

The watcher does not submit enrollment automatically.


## Usage(not using run.sh)

Install all dependencies:

```

pip install -r requirements.txt

```

Activate the virtual environment:

```

source venv/bin/activate

```
Run setup_telegram:

```

python setup_telegram.py

```
Follow telegram setup described above and the instructions.

Run the watcher:

```

python beartracks-watch.py

```

Then:

1. A Chrome window will open.

2. Log in to Bear Tracks manually. It may fail in the first try. Try again.

3. Navigate to your Watch List and Cart page.

4. Make sure the page shows `Open Seats X of Y`.

5. Return to the terminal and press Enter.

6. The script will monitor the page and send Telegram alerts when open seats are detected or logged out due to inactivity.

## Safety Notes

This tool only reads visible page text from a manually logged-in browser session.

It does not:

- store passwords

- bypass MFA or CAPTCHA

- auto-enroll in courses

- send high-frequency requests

- run multiple parallel sessions

Use responsibly and follow your institution's policies.

## License

MIT License
