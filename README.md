# telegram-support-bot

Telegram bot for customer support with group admin chat.

## Features

- Receives messages from users and forwards them to a support group.
- Operators reply in the group and the bot relays the answer back to the user.
- No automated FAQ: only direct communication with human operators.
- Runs via long polling and works well on microcomputers such as Raspberry Pi.

## Installation

```bash
git clone https://github.com/yourusername/telegram-support-bot.git
cd telegram-support-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

1. Create a bot with [@BotFather](https://t.me/BotFather) and obtain the token.
2. Create a support group and find chat IDs of all administrators.
3. Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
# edit .env with your token and comma-separated admin IDs
```

4. Run the bot:

```bash
python bot.py
```

Any message sent to the bot will be forwarded to every administrator. When an operator replies to the forwarded message in the admin chat, the bot sends that reply back to the original user. Users can stop the conversation at any time with the `/cancel` command.
