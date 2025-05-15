class DomainException(Exception):
    """Базовое исключение для доменных ошибок"""

    pass


class CustomPeerFloodError(DomainException):
    """Ошибка спам-блокировки"""

    def __init__(self, phone: str, original_error: Exception):
        self.phone = phone
        self.original_error = original_error
        super().__init__(f"[{phone}] Peer Flood Error: {original_error}")
