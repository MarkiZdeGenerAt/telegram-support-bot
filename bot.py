import logging
import os
from typing import List

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from keyboards import user as user_kb
from services.forwarding import ForwardService


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

forward_service: ForwardService
ADMIN_CHAT_IDS: List[int] = []


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not forward_service.is_allowed(user_id):
        await update.message.reply_text("У вас нет доступа к поддержке.")
        return
    context.user_data["state"] = "waiting"
    await update.message.reply_text(
        "Здравствуйте! Напишите ваш вопрос, и оператор скоро ответит.\n"
        "Для отмены используйте кнопку или команду /cancel.",
        reply_markup=user_kb.cancel_keyboard(),
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    await update.message.reply_text(
        "Диалог завершен. Используйте /start для нового запроса.",
        reply_markup=user_kb.remove_keyboard(),
    )


async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get("state") != "waiting":
        return
    message = update.message
    if not message:
        return
    for admin_id in ADMIN_CHAT_IDS:
        if getattr(message, "text", None):
            forwarded = await context.bot.forward_message(
                chat_id=admin_id,
                from_chat_id=update.effective_chat.id,
                message_id=message.message_id,
            )
        else:
            forwarded = await context.bot.copy_message(
                chat_id=admin_id,
                from_chat_id=update.effective_chat.id,
                message_id=message.message_id,
            )
        forward_service.record_forward(
            admin_id, forwarded.message_id, update.effective_chat.id
        )
        logger.info(
            "Forwarded message %s from %s to admin %s",
            forwarded.message_id,
            update.effective_chat.id,
            admin_id,
        )


async def handle_unsupported(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if context.user_data.get("state") != "waiting":
        return True
    await update.message.reply_text("Этот тип сообщения не поддерживается.")
    return True


async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message.reply_to_message:
        return
    user_chat_id = forward_service.get_user_chat_id(
        update.effective_chat.id, update.message.reply_to_message.message_id
    )
    if user_chat_id:
        await context.bot.copy_message(
            chat_id=user_chat_id,
            from_chat_id=update.effective_chat.id,
            message_id=update.message.message_id,
        )
        logger.info(
            "Relayed reply from admin %s to user %s",
            update.effective_chat.id,
            user_chat_id,
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text("Произошла ошибка, попробуйте позже.")


def main() -> None:
    load_dotenv()
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    admin_ids_str = os.environ.get("ADMIN_CHAT_IDS", "")
    if not admin_ids_str:
        raise RuntimeError("ADMIN_CHAT_IDS is not set")
    global ADMIN_CHAT_IDS, forward_service
    ADMIN_CHAT_IDS = [int(x) for x in admin_ids_str.split(",") if x.strip()]

    db_path = os.environ.get("DB_PATH", "support.db")
    forward_service = ForwardService(db_path)

    try:
        allowed_ids = os.environ.get("ALLOWED_USER_IDS", "")
        for part in allowed_ids.split(","):
            part = part.strip()
            if part:
                forward_service.add_allowed_user(int(part))

        application = Application.builder().token(token).build()

        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("cancel", cancel))
        application.add_handler(
            MessageHandler(
                (filters.GAME | filters.LOCATION) & filters.ChatType.PRIVATE,
                handle_unsupported,
            )
        )
        application.add_handler(
            MessageHandler(filters.ALL & filters.ChatType.PRIVATE, handle_user_message)
        )
        application.add_handler(
            MessageHandler(filters.Chat(ADMIN_CHAT_IDS) & filters.REPLY, handle_admin_reply)
        )

        application.add_error_handler(error_handler)

        application.run_polling()
    finally:
        forward_service.close()


if __name__ == "__main__":
    main()
