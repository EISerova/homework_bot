import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (CheckResponseError, CheckTokensError, ParseStatusError,
                        ResponseError, SendMessageError)

load_dotenv()

PRACTICUM_TOKEN: str = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN: str = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID: int = os.getenv('TELEGRAM_CHAT_ID')
ENDPOINT: str = os.getenv('ENDPOINT')

RESPONSE_KEY: list = ['homeworks', 'current_date']
RETRY_TIME: int = 600
HEADERS: dict = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
HOMEWORK_STATUSES: dict = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(message)s',
    level=logging.DEBUG)


def send_message(bot, message):
    """Отправляет сообщение в Telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info(f'Сообщение {message} отправлено в Telegram')
    except Exception as error:
        logging.error(f'Ошибка при отправке сообщения в Telegram: {error}')
        raise SendMessageError(f'Сообщение не отправилось в Telegram: {error}')


def get_api_answer(current_timestamp):
    """Делает запрос к эндпоинту API-сервиса и возвращает ответ API."""
    timestamp: int = current_timestamp or int(time.time())
    params: dict = {'from_date': timestamp}

    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTPStatus.OK:
            logging.error('Эндпоинт Яндекс.практикума недоступен')
            raise ResponseError('Эндпоинт Яндекс.практикума недоступен')
        return response.json()
    except Exception as error:
        logging.error('Ошибка')
        raise ResponseError('Ошибка при запросе API')


def check_response(response):
    """Проверяет корректность ответа API, возвращает список домашних работ."""
    if type(response['homeworks']) != list:
        logging.error('Ответ не соответствует типам данных Python')
        raise CheckResponseError('Ответ не соответствует типам данных Python')

    for key in RESPONSE_KEY:
        if key not in response:
            logging.error(f'В ответе нет ожидаемого ключа: {key}')
            raise ResponseError(f'В ответе нет ожидаемого ключа: {key}')

    logging.info('Ответ от сервера получен')
    homeworks: list = response.get('homeworks')
    if not homeworks:
        logging.info('Нет обновлений списка домашних работ')

    return homeworks


def parse_status(homework):
    """Извлекает статус проверки, возвращает строку для отправки."""
    homework_name: str = homework['homework_name']
    homework_status: str = homework['status']

    if homework_status not in HOMEWORK_STATUSES:
        logging.error(
            f'Неизвестный статус домашней работы: {homework_status}'
        )
        raise ParseStatusError(
            f'Неизвестный статус домашней работы: {homework_status}'
        )

    verdict: str = HOMEWORK_STATUSES[homework_status]
    logging.info(f'Cтатус домашней работы: {verdict}')

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        return True
    else:
        logging.critical(
            'Отсутствует обязательная переменная окружения'
        )
        return False


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise CheckTokensError('Отсутствует один из токенов')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp: int = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks: list = check_response(response)

            for homework in homeworks:
                message: str = parse_status(homework)
                send_message(bot, message)

            current_timestamp: int = response.get('current_date')
            time.sleep(RETRY_TIME)

        except Exception as error:
            message: str = f'Сбой в работе программы: {error}'
            logging.error(f'Сбой в работе программы: {error}')
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
