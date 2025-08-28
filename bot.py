import os
import logging
from typing import List

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, Update
from aiogram.types.error_event import ErrorEvent

from keyboards import user as user_kb
from services.forwarding import ForwardService


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ADMIN_CHAT_IDS: List[int] = []
forward_service = ForwardService()


class SupportDialog(StatesGroup):
    waiting_for_message = State()


async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.set_state(SupportDialog.waiting_for_message)
    await message.answer(
        "Здравствуйте! Напишите ваш вопрос, и оператор скоро ответит.\n"
        "Для отмены отправьте /cancel.",
        reply_markup=user_kb.cancel_keyboard(),
    )


async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Диалог завершен. Используйте /start для нового запроса.",
        reply_markup=user_kb.remove_keyboard(),
    )


async def handle_user_message(message: Message, state: FSMContext) -> None:
    for admin_id in ADMIN_CHAT_IDS:
        forwarded = await message.forward(admin_id)
        forward_service.record_forward(admin_id, forwarded.message_id, message.chat.id)
        logger.info(
            "Forwarded message %s from %s to admin %s",
            forwarded.message_id,
            message.chat.id,
            admin_id,
        )


async def handle_unsupported(message: Message) -> None:
    await message.answer("Поддерживаются только текстовые сообщения.")


async def handle_admin_reply(message: Message) -> None:
    if message.chat.id not in ADMIN_CHAT_IDS:
        return
    if not message.reply_to_message:
        return
    user_chat_id = forward_service.get_user_chat_id(
        message.chat.id, message.reply_to_message.message_id
    )
    if user_chat_id:
        await message.copy_to(user_chat_id)
        logger.info(
            "Relayed reply from admin %s to user %s",
            message.chat.id,
            user_chat_id,
        )


async def error_handler(event: ErrorEvent) -> None:
    logger.exception("Exception while handling an update:", exc_info=event.exception)


async def main() -> None:
    load_dotenv()
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    admin_ids_str = os.environ.get("ADMIN_CHAT_IDS", "")
    if not admin_ids_str:
        raise RuntimeError("ADMIN_CHAT_IDS is not set")
    global ADMIN_CHAT_IDS
    ADMIN_CHAT_IDS = [int(x) for x in admin_ids_str.split(",") if x.strip()]

    bot = Bot(token)
    dp = Dispatcher()

    dp.message.register(cmd_start, CommandStart(), F.chat.type == "private")
    dp.message.register(cmd_cancel, Command("cancel"), F.chat.type == "private")
    dp.message.register(
        handle_user_message,
        SupportDialog.waiting_for_message,
        F.text,
        F.chat.type == "private",
    )
    dp.message.register(
        handle_unsupported,
        SupportDialog.waiting_for_message,
        F.chat.type == "private",
    )
    dp.message.register(
        handle_admin_reply,
        F.chat.id.in_(ADMIN_CHAT_IDS),
        F.reply_to_message,
    )

    dp.errors.register(error_handler)

    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
