import asyncio
import types
from unittest.mock import AsyncMock, MagicMock

import bot


class DummyMessage:
    def __init__(self, message_id, **kwargs):
        self.message_id = message_id
        for key, value in kwargs.items():
            setattr(self, key, value)


class DummyUpdate:
    def __init__(self, message):
        self.effective_user = types.SimpleNamespace(id=100)
        self.effective_chat = types.SimpleNamespace(id=200)
        self.message = message


def test_photo_forwarding():
    bot.ADMIN_CHAT_IDS = [1]
    bot.forward_service = MagicMock()
    message = DummyMessage(10, photo=[types.SimpleNamespace(file_id="abc")])
    update = DummyUpdate(message)
    context = types.SimpleNamespace(
        user_data={"state": "waiting"},
        bot=types.SimpleNamespace(
            copy_message=AsyncMock(
                return_value=types.SimpleNamespace(message_id=20)
            )
        ),
    )

    asyncio.run(bot.handle_user_message(update, context))

    context.bot.copy_message.assert_awaited_once_with(
        chat_id=1, from_chat_id=200, message_id=10
    )
    bot.forward_service.record_forward.assert_called_once_with(1, 20, 200)


def test_document_forwarding():
    bot.ADMIN_CHAT_IDS = [1]
    bot.forward_service = MagicMock()
    message = DummyMessage(15, document=types.SimpleNamespace(file_id="def"))
    update = DummyUpdate(message)
    context = types.SimpleNamespace(
        user_data={"state": "waiting"},
        bot=types.SimpleNamespace(
            copy_message=AsyncMock(
                return_value=types.SimpleNamespace(message_id=25)
            )
        ),
    )

    asyncio.run(bot.handle_user_message(update, context))

    context.bot.copy_message.assert_awaited_once_with(
        chat_id=1, from_chat_id=200, message_id=15
    )
    bot.forward_service.record_forward.assert_called_once_with(1, 25, 200)

