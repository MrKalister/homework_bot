import logging
import os
import time
import sys

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

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
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logger.info(f'Бот отправил сообщение "{message}"')


def get_api_answer(current_timestamp):
    """Делает запрос эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != 200:
        raise ReferenceError('Статус ответа API не OK')
    return response.json()


def check_response(response):
    """Проверяет ответ API на корректность."""
    key = 'homeworks'
    if isinstance(response[key], dict):
        raise TypeError('В ответе API не словарь')
    if key not in response:
        raise KeyError(f'Ключа "{key}" в словаре нет')
    return response[key]


def parse_status(homework):
    """Извлекает из конкретной домашней работе её статус."""
    if 'homework_name' not in homework:
        raise KeyError('Ключ homework_name отсутствует в homework')
    homework_name = homework['homework_name']
    if 'status' not in homework:
        raise KeyError('Ключ status отсутствует в homework')
    homework_status = homework['status']
    if homework_status not in HOMEWORK_STATUSES:
        raise KeyError(f'Статус {homework_status} неизвестен')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    if not all([PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID]):
        return False
    else:
        return True


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
                status = parse_status(homework[0])
                message = status
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
        else:
            send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()

# Убрал потому что выходила ошибка:
# C901 'main' is too complex (12)
'''
if not PRACTICUM_TOKEN or PRACTICUM_TOKEN is None:
    logger.critical(
        'Отсутствует обязательная переменная окружения:'
        '"PRACTICUM_TOKEN".Программа принудительно остановлена.'
    )
    raise SystemExit
elif not TELEGRAM_TOKEN or TELEGRAM_TOKEN is None:
    logger.critical(
        'Отсутствует обязательная переменная окружения:'
        '"TELEGRAM_TOKEN".Программа принудительно остановлена.'
    )
    raise SystemExit
elif not TELEGRAM_CHAT_ID or TELEGRAM_CHAT_ID is None:
    logger.critical(
        'Отсутствует обязательная переменная окружения:'
        '"TELEGRAM_CHAT_ID".Программа принудительно остановлена.'
    )
    raise SystemExit
else:
'''
