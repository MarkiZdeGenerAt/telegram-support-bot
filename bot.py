import os
import logging
from typing import Dict, Tuple, List

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FORWARD_MAP_KEY = "forward_map"
ADMIN_CHAT_IDS: List[int] = []
WAITING_FOR_MESSAGE = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Здравствуйте! Напишите ваш вопрос, и оператор скоро ответит."
        "\nДля отмены отправьте /cancel."
    )
    return WAITING_FOR_MESSAGE

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    forward_map: Dict[Tuple[int, int], int] = context.bot_data.setdefault(
        FORWARD_MAP_KEY, {}
    )
    for admin_id in ADMIN_CHAT_IDS:
        forwarded = await update.message.forward(admin_id)
        forward_map[(admin_id, forwarded.message_id)] = update.effective_chat.id
        logger.info(
            "Forwarded message %s from %s to admin %s",
            forwarded.message_id,
            update.effective_chat.id,
            admin_id,
        )
    return WAITING_FOR_MESSAGE


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Диалог завершен. Используйте /start для нового запроса.")
    return ConversationHandler.END

async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.id not in ADMIN_CHAT_IDS:
        return
    if not update.message.reply_to_message:
        return
    forward_map: Dict[Tuple[int, int], int] = context.bot_data.get(FORWARD_MAP_KEY, {})
    key = (update.effective_chat.id, update.message.reply_to_message.message_id)
    user_chat_id = forward_map.get(key)
    if user_chat_id:
        await update.message.copy(chat_id=user_chat_id)
        logger.info(
            "Relayed reply from admin %s to user %s", update.effective_chat.id, user_chat_id
        )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Exception while handling an update:", exc_info=context.error)


async def main() -> None:
    load_dotenv()
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    admin_ids_str = os.environ.get("ADMIN_CHAT_IDS", "")
    if not admin_ids_str:
        raise RuntimeError("ADMIN_CHAT_IDS is not set")
    global ADMIN_CHAT_IDS
    ADMIN_CHAT_IDS = [int(x) for x in admin_ids_str.split(",") if x.strip()]

    application = Application.builder().token(token).build()

    user_conversation = ConversationHandler(
        entry_points=[CommandHandler("start", start, filters.ChatType.PRIVATE)],
        states={
            WAITING_FOR_MESSAGE: [
                MessageHandler(
                    filters.ChatType.PRIVATE & ~filters.COMMAND, handle_user_message
                )
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel, filters.ChatType.PRIVATE)],
    )

    application.add_handler(user_conversation)
    application.add_handler(MessageHandler(filters.ALL, handle_admin_reply))
    application.add_error_handler(error_handler)

    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await application.updater.idle()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
