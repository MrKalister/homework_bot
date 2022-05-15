import logging
import os
import time
import sys

import requests
import settings as s
import telegram
from dotenv import load_dotenv
from http import HTTPStatus

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    filemode='a',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] - %(message)s'
)
handler.setFormatter(formatter)


def cache_msg(func):
    """Кэш сообщений."""
    cache = []

    def inner(bot, msg):
        if msg in cache:
            if len(cache) > 15:
                cache.clear()
        else:
            func(bot, msg)
            cache.append(msg)
        logger.info(msg)
    return inner


@cache_msg
def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info(f'Бот отправил сообщение "{message}"')
    except telegram.error.TelegramError as error:
        logger.error(f'Бот не отправил сообщение "{message}": {error}')


def get_api_answer(current_timestamp):
    """Делает запрос эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(s.ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != HTTPStatus.OK:
        raise ReferenceError('Статус ответа API не OK')
    return response.json()


def check_response(response):
    """Проверяет ответ API на корректность."""
    if not isinstance(response, dict):
        raise TypeError('В ответе API нет словаря')
    if 'homeworks' not in response:
        raise KeyError('Ключа "homeworks" в словаре нет')
    if not isinstance(response['homeworks'], list):
        raise TypeError('По ключу "homeworks" не получен список')
    return response['homeworks']


def parse_status(homework):
    """Извлекает из конкретной домашней работе её статус."""
    if 'homework_name' not in homework:
        raise KeyError('Ключ homework_name отсутствует в homework')
    homework_name = homework['homework_name']
    if 'status' not in homework:
        raise KeyError('Ключ status отсутствует в homework')
    homework_status = homework['status']
    if homework_status not in s.HOMEWORK_STATUSES:
        raise KeyError(f'Статус {homework_status} неизвестен')
    verdict = s.HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    return all([PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical(
            'Отсутствует обязательная переменная окружения.'
            'Программа принудительно остановлена.'
        )
        raise SystemExit

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if not homework:
                message = "На данный момент обновлений нет"
            else:
                message = parse_status(homework[0])
            current_timestamp = response['current_date']
        except ReferenceError as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(error)
        except KeyError as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(error)
        except TypeError as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(error)
        finally:
            send_message(bot, message)
            time.sleep(s.RETRY_TIME)


if __name__ == '__main__':
    main()
