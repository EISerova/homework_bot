class CheckResponseError(Exception):
    """Несоответствие ответа типу данных Python."""

    pass


class ResponseError(Exception):
    """Отсутствие в ответе API ожидаемого ключа."""

    pass


class SendMessageError(Exception):
    """Сообщение не отправилось в Telegram."""

    pass


class ParseStatusError(Exception):
    """Неизвестный статус домашней работы."""

    pass


class CheckTokensError(Exception):
    """Отсутствует один из токенов."""

    pass


class GetApiError(Exception):
    """Ошибка при запросе API."""

    pass
