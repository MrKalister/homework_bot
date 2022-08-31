# homework_bot
A telegram bot checks the status of my homework.
The bot uses API Yandex.practicum.
The bot polls [a endpoint](https://practicum.yandex.ru/api/user_api/homework_statuses/) every 600 seconds and check the status. It must match one of the following:
* approved,
* reviewing,
* rejected.

The bot also cheks errors when polling the server and logging.
The bot send message if change status a last homework or detects an error.
