# homework_bot
The telegram bot checks the status of my homework.
The bot uses API Yandex.practicum.
The bot polls [a endpoint](https://practicum.yandex.ru/api/user_api/homework_statuses/) every 600 seconds and check the status. It must match one of the following:
* approved,
* reviewing,
* rejected.
