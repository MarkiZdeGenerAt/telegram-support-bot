# Telegram Support Bot

Asynchronous Telegram bot for customer support built on
[python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
(v20+). Users send messages to the bot and operators reply from a private
support chat. Mapping between forwarded messages and users is stored in a
SQLite database.

## Features

- Forward user messages to one or more admin chats and relay replies back.
- SQLite storage for message mapping and access control.
- Optional whitelist of users allowed to contact support.
- Graceful error handling and friendly replies with keyboards.

## Installation

```bash
git clone https://github.com/yourusername/telegram-support-bot.git
cd telegram-support-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` and fill your values:

```bash
cp .env.example .env
```

Required variables:

- `TELEGRAM_BOT_TOKEN` – token from [@BotFather](https://t.me/BotFather)
- `ADMIN_CHAT_IDS` – comma separated chat IDs of admins

Optional:

- `ALLOWED_USER_IDS` – comma separated user IDs with access to support.
  When empty, everyone can start a chat.
- `DB_PATH` – path to SQLite database file (default `support.db`).

## Usage

```bash
python bot.py
```

Any text message sent to the bot is forwarded to all admins. Operators reply to
the forwarded message in the admin chat; the bot copies the reply back to the
original user. Users can finish the conversation with the `/cancel` command or
by pressing the *Отмена* button.

## Tests

Run unit tests with:

```bash
pytest
```
