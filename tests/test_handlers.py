import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import bot
from services.forwarding import ForwardService

try:
    from telegram.ext import ApplicationBuilder
    from telegram.ext._testutils import DummyUpdate, DummyMessage
except Exception:  # pragma: no cover - fall back for local env
    from telegram.ext import ApplicationBuilder  # type: ignore

    class DummyMessage:
        def __init__(self, message_id, text=None, reply_to_message=None):
            self.message_id = message_id
            self.text = text
            self.reply_to_message = reply_to_message
            self.reply_text = AsyncMock()

    class DummyUpdate:
        def __init__(self, message, user_id=100, chat_id=200):
            self.effective_user = SimpleNamespace(id=user_id)
            self.effective_chat = SimpleNamespace(id=chat_id)
            self.message = message


@pytest.fixture
def application():
    return ApplicationBuilder().token("TOKEN").build()


def test_start_sets_state_and_replies(application):
    bot.forward_service = ForwardService(":memory:")
    message = DummyMessage(1)
    update = DummyUpdate(message)
    context = SimpleNamespace(user_data={}, bot=application.bot)
    asyncio.run(bot.start(update, context))
    assert context.user_data["state"] == "waiting"
    message.reply_text.assert_awaited_once()
    assert message.reply_text.await_args.args[0].startswith("Здравствуйте!")


def test_cancel_clears_state(application):
    message = DummyMessage(2)
    update = DummyUpdate(message)
    context = SimpleNamespace(user_data={"state": "waiting"}, bot=application.bot)
    asyncio.run(bot.cancel(update, context))
    assert context.user_data == {}
    message.reply_text.assert_awaited_once()
    assert "Диалог завершен" in message.reply_text.await_args.args[0]


def test_handle_user_message_records_forward(application):
    bot.ADMIN_CHAT_IDS = [1]
    bot.forward_service = ForwardService(":memory:")
    message = DummyMessage(5, text="hi")
    update = DummyUpdate(message)
    forwarded = SimpleNamespace(message_id=50)
    application.bot.forward_message = AsyncMock(return_value=forwarded)
    context = SimpleNamespace(user_data={"state": "waiting"}, bot=application.bot)
    asyncio.run(bot.handle_user_message(update, context))
    application.bot.forward_message.assert_awaited_once_with(
        chat_id=1, from_chat_id=200, message_id=5
    )
    assert bot.forward_service.get_user_chat_id(1, 50) == 200


def test_handle_admin_reply_uses_mapping(application):
    bot.forward_service = ForwardService(":memory:")
    bot.forward_service.record_forward(1, 10, 200)
    reply_to = SimpleNamespace(message_id=10)
    message = DummyMessage(20, text="hi", reply_to_message=reply_to)
    update = DummyUpdate(message, user_id=1, chat_id=1)
    application.bot.copy_message = AsyncMock()
    context = SimpleNamespace(bot=application.bot)
    asyncio.run(bot.handle_admin_reply(update, context))
    application.bot.copy_message.assert_awaited_once_with(
        chat_id=200, from_chat_id=1, message_id=20
    )
