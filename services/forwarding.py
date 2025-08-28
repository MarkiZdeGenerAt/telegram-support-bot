from typing import Dict, Tuple, Optional

ForwardMap = Dict[Tuple[int, int], int]

class ForwardService:
    """Service to keep track of message forwards between admins and users."""

    def __init__(self) -> None:
        self._map: ForwardMap = {}

    def record_forward(self, admin_id: int, forwarded_message_id: int, user_chat_id: int) -> None:
        self._map[(admin_id, forwarded_message_id)] = user_chat_id

    def get_user_chat_id(self, admin_id: int, forwarded_message_id: int) -> Optional[int]:
        return self._map.get((admin_id, forwarded_message_id))
