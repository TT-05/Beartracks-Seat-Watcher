import requests

from pathlib import Path

ENV_PATH = Path(".env")

def main():

    print("Telegram Bot Setup")

    print("------------------")

    print()

    print("Before continuing:")

    print("1. Open Telegram")

    print("2. Search @BotFather")

    print("3. Send /newbot")

    print("4. Copy the bot token")

    print()

    bot_token = input("Paste your Telegram BOT_TOKEN here: ").strip()

    if not bot_token:

        print("BOT_TOKEN cannot be empty.")

        return

    print()

    print("Now open your Telegram bot and send:")

    print("/start")

    print("test")

    print()

    input("After sending a message to your bot, press Enter here...")

    url = f"https://api.telegram.org/bot{bot_token}/getUpdates?offset=-1"

    try:

        response = requests.get(url, timeout=15)

        response.raise_for_status()

        data = response.json()

    except Exception as e:

        print(f"Failed to call Telegram API: {e}")

        return

    result = data.get("result", [])

    if not result:

        print("No updates found.")

        print("Make sure you sent /start or test to your bot.")

        print("Then run this script again.")

        return

    message = result[-1].get("message", {})

    chat = message.get("chat", {})

    chat_id = chat.get("id")

    if not chat_id:

        print("Could not find chat_id in Telegram response.")

        return

    env_text = (

        f'TELEGRAM_BOT_TOKEN="{bot_token}"\n'

        f'TELEGRAM_CHAT_ID="{chat_id}"\n'

    )

    ENV_PATH.write_text(env_text)

    print()

    print("Telegram setup complete.")

    print(f"Your chat_id is: {chat_id}")

    print("Saved to .env")

    print()

    print("Important: do not upload .env to GitHub.")

if __name__ == "__main__":

    main()
