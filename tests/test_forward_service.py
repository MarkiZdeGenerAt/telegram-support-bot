import os
import sqlite3
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.forwarding import ForwardService


def test_record_and_get_forward():
    service = ForwardService(":memory:")
    service.record_forward(admin_id=1, forwarded_message_id=123, user_chat_id=42)
    assert service.get_user_chat_id(1, 123) == 42


def test_access_control():
    service = ForwardService(":memory:")
    assert service.is_allowed(1)  # no restrictions
    service.add_allowed_user(1)
    service.add_allowed_user(2)
    assert service.is_allowed(1)
    assert not service.is_allowed(3)


def test_close_prevents_further_operations():
    service = ForwardService(":memory:")
    service.close()
    with pytest.raises(sqlite3.ProgrammingError):
        service.record_forward(admin_id=1, forwarded_message_id=1, user_chat_id=1)
