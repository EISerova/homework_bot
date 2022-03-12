import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv
from requests.exceptions import RequestException

from exceptions import (ResponseDeniedError, ResponseKeyError,
                        ResponseStatusError)

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TOKENS = ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORKS_KEY = 'homeworks'
ADDITIONAL_KEY = 'current_date'
DENIED_KEY = ['error', 'code']

RETRY_TIME = 600

HOMEWORK_VERDICT = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

INFO_SEND_MSG = 'Сообщение "{message}" отправлено в Telegram'
ERROR_SEND_MSG = 'Сообщение не отправлено Telegram: {error}'
ERROR_ENDPOINT = (
    'Сервер вернул некорректный код ответа: {response},'
    'параметры запроса: headers - {headers}, params – {params}'
)
ERROR_GET_API = (
    'Запрос не выполнен: {error},'
    'параметры запроса: headers - {headers}, params – {params}'
)
ERROR_RESPONSE_TYPE = 'json-ответ - не словарь, полученный тип данных: {type}'
ERROR_HOMEWORKS_TYPE = 'В json-ответе тип "homeworks" - не список, а: {type}'
ERROR_RESPONSE_KEY = 'Получен некорректный ответ: нет ключа {key}'
INFO_RESPONSE = 'Ответ от сервера получен'
INFO_HOMEWORKS = 'В списке домашних работе нет обновлений'
ERROR_STATUS = 'Неизвестный статус домашней работы: {status}'
INFO_STATUS = 'Изменился статус проверки работы "{name}": {verdict}'
CRITICAL_TOKEN = 'Отсутствует обязательный токен: {token}'
ERROR_MAIN = 'Работа программы остановлена: {error}'
RESPONSE_DENIED = 'Запрос отклонен сервером, причина: {denied}'


def send_message(bot, message):
    """Отправляет сообщение в Telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        log.info(INFO_SEND_MSG.format(message=message))
    except Exception as err:
        log.exception(ERROR_SEND_MSG.format(error=err))


def get_api_answer(current_timestamp):
    """Делает запрос к эндпоинту API-сервиса и возвращает ответ."""
    params = {'from_date': current_timestamp}

    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)

    except RequestException as err:
        raise requests.HTTPError(
            ERROR_GET_API.format(error=err, headers=HEADERS, params=params)
        )

    if response.status_code != HTTPStatus.OK:
        raise ResponseStatusError(
            ERROR_ENDPOINT.format(
                response=response.status_code, headers=HEADERS, params=params
            )
        )

    response_json: dict = response.json()

    for key in DENIED_KEY:
        if key in response_json:
            raise ResponseDeniedError(
                RESPONSE_DENIED.format(denied=response_json[key])
            )

    return response_json


def check_response(response):
    """Проверяет корректность ответа API, возвращает список домашних работ."""
    if not isinstance(response, dict):
        raise TypeError(
            ERROR_RESPONSE_TYPE.format(type=type(response))
        )
    if globals()['HOMEWORKS_KEY'] not in response:
        raise ResponseKeyError(
            ERROR_RESPONSE_KEY.format(key=globals()['HOMEWORKS_KEY'])
        )
    if globals()['ADDITIONAL_KEY'] not in response:
        log.error(ERROR_RESPONSE_KEY.format(key=globals()['HOMEWORKS_KEY']))

    homeworks: list = response.get('homeworks')

    if not isinstance(homeworks, list):
        raise TypeError(ERROR_HOMEWORKS_TYPE.format(type=type(homeworks)))

    log.info(INFO_RESPONSE)

    return homeworks


def parse_status(homework):
    """Извлекает статус проверки, возвращает строку для отправки."""
    name: str = homework['homework_name']
    status: str = homework['status']

    if status not in HOMEWORK_VERDICT:
        raise KeyError(ERROR_STATUS.format(status=status))
    return INFO_STATUS.format(name=name, verdict=HOMEWORK_VERDICT[status])


def check_tokens():
    """Проверяет доступность переменных окружения."""
    for token in TOKENS:
        if not globals()[token]:
            logging.critical(CRITICAL_TOKEN.format(token=token))
            return False
        return True


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise NameError(CRITICAL_TOKEN, exc_info=True)

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            response: dict = get_api_answer(current_timestamp)
            homework: list = check_response(response)
            if homework:
                send_message(bot, parse_status(homework[0]))
            current_timestamp: int = response.get(
                'current_date', current_timestamp
            )
        except Exception as error:
            log.exception(ERROR_MAIN.format(error=error), exc_info=True)
            send_message(bot, ERROR_MAIN.format(error=error))
        time.sleep(RETRY_TIME)


if __name__ == '__main__':
    """Настройки логгера."""
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s - %(funcName)s - %(lineno)d'
    )

    fh = logging.FileHandler(__file__ + '.log')
    ch = logging.StreamHandler()

    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    log.addHandler(fh)
    log.addHandler(ch)

    """Основная функция"""
    main()

else:
    log = logging.getLogger(__name__)
