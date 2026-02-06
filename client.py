"""
TCP-клиент для отправки PING-запросов серверу.

Клиент реализует протокол:
1. Подключается к серверу на 127.0.0.1:8888
2. Отправляет сообщения "[номер] PING\\n" со случайными интервалами 300-3000мс
3. Получает ответы от сервера в формате "[номер_ответа/номер_запроса] PONG (ID_клиента)\\n"
4. Получает keepalive сообщения: "[номер] keepalive\\n"
5. Ведет лог в формате CSV со временем отправки и получения
6. Отслеживает таймауты (если ответ не пришел за 5 секунд)

┌─────────────────────────────────────────────────────┐
│                  EVENT LOOP                         │
│             (один процесс, один поток)              │
├─────────────────────────────────────────────────────┤
│  ЗАДАЧА 1: send_pings()                             │
│    ▼                                                │
│    • Жду 1.5 секунды... (await sleep)               │
│    • Отправляю "[0] PING"                           │
│    • Сохраняю время в pending[0]                    │
│    • Логирую отправку                               │
│    • Жду 2.3 секунды...                             │
│    • Отправляю "[1] PING"                           │
│    • И т.д.                                         │
│                                                     │
│  ЗАДАЧА 2: receive_responses()                      │
│    ▼                                                │
│    • Жду ответ от сервера... (await readline)       │
│    • Получил "[0/0] PONG (1)"                       │
│    • Ищу pending[0] - нашел!                        │
│    • Логирую: время отправки → время получения      │
│    • Удаляю pending[0]                              │
│    • Возвращаюсь ждать следующий ответ              │
│                                                     │
│  ЗАДАЧА 3: check_timeouts()                         │
│    ▼                                                │
│    • Жду 2 секунды... (await sleep)                 │
│    • Проверяю все pending запросы                   │
│    • pending[1] ждет уже 6 секунд → ТАЙМАУТ!        │
│    • Логирую таймаут                                │
│    • Удаляю pending[1]                              │
│    • Возвращаюсь ждать 2 секунды                    │
│                                                     │
│  ЗАДАЧА 4: Основной таймер (await sleep(300))       │
│    ▼                                                │
│    • Отсчитываю 5 минут...                          │
│    • Когда время вышло → cancel всем задачам        │
│    • Закрываю соединение                            │
└─────────────────────────────────────────────────────┘
"""

import asyncio
import random
import datetime
import sys
from typing import Dict, Optional


class SimpleClient:
    """
    TCP-клиент для обмена PING/PONG сообщениями с сервером.

    Каждый клиент:
    1. Имеет уникальный номер (client_num)
    2. Поддерживает свое соединение с сервером
    3. Отправляет PING сообщения с автоинкрементируемым номером
    4. Обрабатывает ответы сервера (PONG и keepalive)
    5. Отслеживает таймауты неответивших запросов
    """

    def __init__(self, client_num: int) -> None:
        """
        Инициализирует клиента с заданным номером.

        Args:
            client_num: int - номер клиента (1, 2, ...), используется для именования лог-файлов

        Атрибуты:
            client_num: int - идентификатор клиента
            request_num: int - счетчик отправленных запросов (начинается с 0)
            pending: Dict[int, datetime.datetime] - словарь ожидающих ответа запросов:
                ключ: номер запроса, значение: время отправки
        """
        self.client_num: int = client_num  # Номер клиента для идентификации
        self.request_num: int = (
            0  # Счетчик отправленных запросов (начинается с 0)
        )
        self.pending: Dict[int, datetime.datetime] = (
            {}
        )  # словарь ожидающих ответов: {0: время_отправки_0, 1: время_отправки_1}

    async def start(self) -> None:
        """
        Основной метод запуска клиента.

        Последовательность действий:
        1. Подключается к серверу 127.0.0.1:8888
        2. Запускает задачу отправки PING сообщений (send_pings)
        3. Запускает задачу получения ответов (receive_responses)
        4. Работает 5 минут (300 секунд)
        5. Корректно останавливает все задачи и закрывает соединение

        Исключения:
            ConnectionRefusedError: если сервер недоступен
            ConnectionError: при разрыве соединения во время работы
        """
        try:
            # Установка TCP соединения с сервером
            reader: asyncio.StreamReader
            writer: (
                asyncio.StreamWriter
            )  # просто создали две переменных, да так можно
            reader, writer = await asyncio.open_connection('127.0.0.1', 8888)
            print(f"Клиент {self.client_num} подключился")
        except (ConnectionRefusedError, ConnectionError):
            print(f"Клиент {self.client_num}: не могу подключиться к серверу")
            print("Убедитесь, что сервер запущен: python server.py")
            return  # Ранний выход (early return)

        # Запускаем асинхронные задачи
        send_task: asyncio.Task[None] = asyncio.create_task(
            self.send_pings(writer)
        )
        recv_task: asyncio.Task[None] = asyncio.create_task(
            self.receive_responses(reader)
        )

        # Ждем 5 минут (300 секунд) работы клиента
        await asyncio.sleep(300)

        # Корректная остановка задач и закрытие соединения
        send_task.cancel()
        recv_task.cancel()
        writer.close()

    async def send_pings(self, writer: asyncio.StreamWriter) -> None:
        """
        Отправляет PING сообщения серверу со случайными интервалами.

        Работает в бесконечном цикле:
        1. Ждет случайное время 0.3-3.0 секунды (300-3000 мс)
        2. Формирует сообщение формата "[номер] PING\\n"
        3. Сохраняет время отправки для отслеживания таймаутов
        4. Отправляет сообщение серверу
        5. Логирует отправку в файл
        6. Увеличивает счетчик запросов

        Args:
            writer: asyncio.StreamWriter - поток для отправки данных серверу

        Формат сообщения:
            "[0] PING\\n"
            "[1] PING\\n"
            "[2] PING\\n"
            ...
        """
        while True:
            # Случайная задержка между сообщениями: 300-3000 мс
            await asyncio.sleep(random.uniform(0.3, 3.0))

            # Формируем сообщение с переводом строки в конце \n это бай 0x0A в ASCII таблице
            message: str = f"[{self.request_num}] PING\n"
            send_time: datetime.datetime = datetime.datetime.now()

            # Сохраняем время отправки для последующего сопоставления с ответом
            self.pending[self.request_num] = send_time

            # Отправка сообщения серверу
            writer.write(message.encode(encoding="utf-8"))
            await writer.drain()

            # Логирование отправленного сообщения
            self.log_send(message.strip(), send_time)

            self.request_num += 1

    async def receive_responses(self, reader: asyncio.StreamReader) -> None:
        """
        Получает и обрабатывает ответы от сервера.

        Работает в бесконечном цикле:
        1. Читает строку из потока (до символа \\n)
        2. Определяет тип сообщения (PONG или keepalive)
        3. Для PONG - сопоставляет с отправленным запросом
        4. Логирует полученный ответ
        5. Удаляет запрос из ожидающих при получении ответа

        Args:
            reader: asyncio.StreamReader - поток для чтения данных от сервера

        Обрабатываемые форматы:
            PONG: "[0/0] PONG (1)\\n" - ответ на конкретный запрос
            keepalive: "[5] keepalive\\n" - периодическое сообщение от сервера
        """
        while True:
            data: bytes = await reader.readline()
            if not data:  # Сервер закрыл соединение
                print(f"Клиент {self.client_num}: сервер закрыл соединение")
                break

            response: str = data.decode(encoding="utf-8").strip()
            recv_time: datetime.datetime = datetime.datetime.now()

            if 'keepalive' in response:
                # Keepalive сообщение (периодическая проверка от сервера)
                self.log_keepalive(response, recv_time)
            elif 'PONG' in response:
                # Ответ на PING запрос
                try:
                    # Извлекаем номер запроса из ответа
                    # Формат: "[номер_ответа/номер_запроса] PONG (ID_клиента)"
                    req_num: int = int(response.split('/')[1].split(']')[0])

                    if req_num in self.pending:
                        send_time: datetime.datetime = self.pending[req_num]
                        self.log_response(
                            message=f"[{req_num}] PING",
                            send_time=send_time,
                            response=response,
                            recv_time=recv_time,
                        )
                        # Удаляем запрос из ожидающих, так как получили ответ
                        del self.pending[req_num]
                except (ValueError, IndexError):
                    # Некорректный формат ответа - игнорируем
                    pass

    def log_send(self, message: str, send_time: datetime.datetime) -> None:
        """
        Логирует отправленное сообщение в CSV формате.

        Формат записи:
            ГГГГ-ММ-ДД;ЧЧ:ММ:СС.ммм;сообщение

        Пример:
            2024-01-15;14:30:25.123;[0] PING

        Args:
            message: str - текст отправленного сообщения
            send_time: datetime.datetime - время отправки сообщения
        """
        date_str: str = datetime.datetime.now().strftime('%Y-%m-%d')
        time_str: str = send_time.strftime('%H:%M:%S.%f')[:-3]
        with open(f'client_{self.client_num}.log', 'a', encoding='UTF-8') as f:
            f.write(f"{date_str};{time_str};{message}\n")

    def log_keepalive(
        self, response: str, recv_time: datetime.datetime
    ) -> None:
        """
        Логирует полученное keepalive сообщение в CSV формате.

        Формат записи (первые три поля пустые для keepalive):
            ГГГГ-ММ-ДД;;;ЧЧ:ММ:СС.ммм;keepalive_сообщение

        Пример:
            2024-01-15;;;14:30:30.500;[5] keepalive

        Args:
            response: str - текст keepalive сообщения
            recv_time: datetime.datetime - время получения сообщения
        """
        date_str: str = datetime.datetime.now().strftime('%Y-%m-%d')
        time_str: str = recv_time.strftime('%H:%M:%S.%f')[:-3]
        with open(f'client_{self.client_num}.log', 'a', encoding='UTF-8') as f:
            f.write(f"{date_str};;;{time_str};{response}\n")

    def log_response(
        self,
        message: str,
        send_time: datetime.datetime,
        response: str,
        recv_time: datetime.datetime,
    ) -> None:
        """
        Логирует полученный ответ на PING запрос в CSV формате.

        Формат записи:
            ГГГГ-ММ-ДД;ЧЧ:ММ:СС.ммм_отправки;запрос;ЧЧ:ММ:СС.ммм_получения;ответ

        Пример:
            2024-01-15;14:30:25.123;[0] PING;14:30:25.567;[0/0] PONG (1)

        Args:
            message: str - текст исходного запроса
            send_time: datetime.datetime - время отправки запроса
            response: str - текст полученного ответа
            recv_time: datetime.datetime - время получения ответа
        """
        date_str: str = datetime.datetime.now().strftime('%Y-%m-%d')
        send_str: str = send_time.strftime('%H:%M:%S.%f')[:-3]
        recv_str: str = recv_time.strftime('%H:%M:%S.%f')[:-3]
        with open(f'client_{self.client_num}.log', 'a', encoding='UTF-8') as f:
            f.write(f"{date_str};{send_str};{message};{recv_str};{response}\n")


async def check_timeouts(client: SimpleClient, client_num: int) -> None:
    """
    Фоновая задача для проверки таймаутов ожидающих ответов.

    Работает в бесконечном цикле:
    1. Проверяет каждые 2 секунды ожидающие запросы
    2. Для запросов, которые ждут больше 5 секунд:
       - Логирует таймаут
       - Удаляет запрос из ожидающих

    Args:
        client: SimpleClient - экземпляр клиента для проверки
        client_num: int - номер клиента для именования лог-файла
    """
    while True:
        await asyncio.sleep(2)
        now: datetime.datetime = datetime.datetime.now()

        # Создаем копию словаря для безопасной итерации
        pending_items = list(client.pending.items())

        for req_num, send_time in pending_items:
            # Если с момента отправки прошло больше 5 секунд
            if (now - send_time).total_seconds() > 5:
                # Логируем таймаут
                date_str: str = datetime.datetime.now().strftime('%Y-%m-%d')
                send_str: str = send_time.strftime('%H:%M:%S.%f')[:-3]

                # Время таймаута = время отправки + 5 секунд
                timeout_time: datetime.datetime = (
                    send_time + datetime.timedelta(seconds=5)
                )
                timeout_str: str = timeout_time.strftime('%H:%M:%S.%f')[:-3]

                with open(
                    f'client_{client_num}.log', 'a', encoding='UTF-8'
                ) as f:
                    f.write(
                        f"{date_str};{send_str};[{req_num}] PING;{timeout_str};(таймаут)\n"
                    )

                # Удаляем запрос из ожидающих
                del client.pending[req_num]


async def main(client_num: int) -> None:
    """
    Основная асинхронная функция запуска клиента.

    Args:
        client_num: int - номер клиента, передается из аргументов командной строки

    Процесс:
        1. Создает экземпляр SimpleClient
        2. Запускает фоновую задачу проверки таймаутов
        3. Запускает основную логику клиента
        4. Корректно останавливает задачу проверки таймаутов
    """
    client: SimpleClient = SimpleClient(client_num)
    timeout_task = None
    try:
        # Запускаем проверку таймаутов в фоне
        timeout_task: asyncio.Task[None] = asyncio.create_task(
            check_timeouts(client, client_num)
        )

        # Запускаем основную логику клиента
        await client.start()

    finally:
        # Останавливаем проверку таймаутов
        if timeout_task:
            timeout_task.cancel()


if __name__ == "__main__":
    """
    Точка входа для запуска клиента напрямую.

    При запуске скрипта:
    1. Определяет номер клиента из аргументов командной строки
    2. Очищает соответствующий лог-файл
    3. Запускает асинхронный цикл с клиентом

    Использование:
        python client.py 1  # Запуск клиента №1
        python client.py 2  # Запуск клиента №2
    """
    # Получаем номер клиента из аргументов командной строки
    if len(sys.argv) > 1:
        client_num: int = int(sys.argv[1])
    else:
        client_num: int = 1  # Значение по умолчанию - клиент №1

    # Очищаем лог-файл при каждом запуске
    open(f'client_{client_num}.log', 'w').close()

    # Запускаем асинхронный цикл с клиентом
    asyncio.run(main(client_num))
