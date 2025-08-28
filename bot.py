import os
from typing import Dict
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

FORWARD_MAP_KEY = "forward_map"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Здравствуйте! Напишите ваш вопрос, и оператор скоро ответит.")

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    admin_chat_id = int(os.environ["ADMIN_CHAT_ID"])
    forwarded = await update.message.forward(admin_chat_id)
    forward_map: Dict[int, int] = context.bot_data.setdefault(FORWARD_MAP_KEY, {})
    forward_map[forwarded.message_id] = update.effective_chat.id

async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    admin_chat_id = int(os.environ["ADMIN_CHAT_ID"])
    if update.effective_chat.id != admin_chat_id:
        return
    if not update.message.reply_to_message:
        return
    forward_map: Dict[int, int] = context.bot_data.get(FORWARD_MAP_KEY, {})
    user_chat_id = forward_map.get(update.message.reply_to_message.message_id)
    if user_chat_id:
        await update.message.copy(chat_id=user_chat_id)

async def main() -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ChatType.PRIVATE, handle_user_message))
    application.add_handler(MessageHandler(filters.ALL, handle_admin_reply))

    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await application.updater.idle()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
