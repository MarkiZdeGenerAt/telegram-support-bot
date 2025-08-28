import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.forwarding import ForwardService


def test_record_and_get_forward():
    service = ForwardService()
    service.record_forward(admin_id=1, forwarded_message_id=123, user_chat_id=42)
    assert service.get_user_chat_id(1, 123) == 42


def test_get_user_chat_id_missing():
    service = ForwardService()
    assert service.get_user_chat_id(1, 999) is None
