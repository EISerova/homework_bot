class ResponseKeyError(Exception):
    """Получен некорректный ответ: нет ключа."""

    pass


class ResponseStatusError(Exception):
    """Сервер вернул некорректный код ответа."""

    pass


class ResponseDeniedError(Exception):
    """Запрос отклонен сервером."""

    pass
