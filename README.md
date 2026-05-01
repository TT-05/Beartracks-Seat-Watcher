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

- Includes a Telegram setup helper

- Does not store your CCID or password

- Does not auto-enroll

- Does not bypass MFA, CAPTCHA, or login protection

## Requirements

- macOS

- Python 3

- Google Chrome

- Telegram account

- Telegram bot token

## Installation

Clone the repository:

```
git clone https://github.com/TT-05/Beartracks-Seat-Watcher.git

cd beartracks-seat-watcher

```

Run the setup script:

```

chmod +x setup.sh

./setup.sh

```

This will create a virtual environment, install Python dependencies, and install Playwright Chrome support.

## Telegram Setup

Create a Telegram bot manually using `@BotFather`.

In Telegram:

1. Search `@BotFather`

2. Send `/newbot`

3. Follow the instructions

4. Copy the bot token

Then activate the virtual environment:

```

source venv/bin/activate

```

Run the Telegram setup helper:

```

python setup_telegram.py

```

The helper will ask for your bot token, ask you to send `/start` or `test` to your bot, then automatically find your `chat_id` and save both values into a local `.env` file.


## Usage

Activate the virtual environment:

```

source venv/bin/activate

```

Run the watcher:

```

python beartracks-watch.py

```

Then:

1. A Chrome window will open.

2. Log in to Bear Tracks manually.

3. Navigate to your Watch List or Cart page.

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
