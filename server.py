"""
TCP-сервер для обработки PING-запросов от клиентов.

Сервер реализует протокол:
1. Принимает сообщения в формате "[номер] PING\\n" от клиентов
2. С 10% вероятностью игнорирует запрос
3. В остальных случаях отвечает "[номер_ответа/номер_запроса] PONG (ID_клиента)\\n"
4. Каждые 5 секунд отправляет всем keepalive: "[номер] keepalive\\n"
5. Ведет лог в формате CSV: дата;время_получения;запрос;время_отправки;ответ

┌─────────────────────────────────────────────────────┐
│                   EVENT LOOP                        │
│  (одна программа, один процесс, один главный цикл)  │
├─────────────────────────────────────────────────────┤
│  ЗАДАЧА 1: server.serve_forever()                   │
│    ▼                                                │
│    • Жду нового клиента...                          │
│    • Клиент подключился!                            │
│    • Запускаю handle_client() для него  НОВАЯ ЗАДАЧА│
│    • Возвращаюсь ждать следующего клиента           │
│                                                     │
│  ЗАДАЧА 2: keepalive()                              │
│    ▼                                                │
│    • Жду 5 секунд... (await asyncio.sleep(5))       │
│    • Прошло 5 секунд!                               │
│    • Отправляю keepalive всем клиентам              │
│    • Возвращаюсь ждать еще 5 секунд                 │
│                                                     │
│  ЗАДАЧА 3: handle_client() для Клиента 1            │
│    ▼                                                │
│    • Жду сообщение от клиента...                    │
│    • Получил "[0] PING"                             │
│    • Обрабатываю...                                 │
│    • Отправляю ответ                                │
│    • Возвращаюсь ждать следующее сообщение          │
│                                                     │
│  ЗАДАЧА 4: handle_client() для Клиента 2            │
│    ▼                                                │
│    • Тоже жду сообщение...                          │
│    • И т.д.                                         │
└─────────────────────────────────────────────────────┘


"""

import asyncio
import random
import datetime
from typing import Dict, Optional


class Server:
    """TCP-сервер для обработки PING/PONG сообщений."""

    def __init__(self) -> None:
        """
        Инициализирует TCP-сервер.

        Атрибуты:
            response_counter: int - сквозная нумерация всех ответов сервера
            clients: Dict[asyncio.StreamWriter, int] - словарь подключений: writer -> client_id
            next_client_id: int - следующий доступный ID для нового клиента
        """
        self.response_counter: int = 0  # Сквозная нумерация всех ответов
        self.clients: Dict[asyncio.StreamWriter, int] = (
            {}
        )  # writer -> client_id
        self.next_client_id: int = 1  # ID следующего клиента

    async def handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """
        Обрабатывает подключение одного клиента.

        Эта корутина запускается для каждого нового клиента и:
        1. Регистрирует клиента с уникальным ID
        2. Читает сообщения от клиента построчно
        3. Обрабатывает PING запросы
        4. Отправляет PONG ответы
        5. Корректно закрывает соединение при отключении

        Args:
            reader: asyncio.StreamReader - поток для чтения данных от клиента
            writer: asyncio.StreamWriter - поток для отправки данных клиенту

        Процесс работы:
            КЛИЕНТ -> СЕРВЕР: "[0] PING\\n"
            СЕРВЕР -> КЛИЕНТ: "[0/0] PONG (1)\\n" (после задержки 100-1000мс)
        """
        client_id: int = (
            self.next_client_id
        )  # хитрая система увеличения id клиента
        # зафиксировали в словаре
        self.clients[writer] = client_id
        self.next_client_id += 1  # и вот он стал на единицу больше

        print(f"Клиент {client_id} подключился")

        try:
            while True:
                # Чтение сообщения от клиента (ждет до символа \\n -
                # это и есть в аски таблице байт 0x0a перевода на новую строку LF)
                data: bytes = await reader.readline()
                if not data:  # Клиент отключился
                    break

                # Декодируем Убираем пробелы и \\n
                message: str = data.decode().strip()
                # Время получения
                receive_time: datetime.datetime = datetime.datetime.now()

                # 10% шанс игнорировать запрос
                if random.random() < 0.1:
                    self.log_ignored(message, receive_time)
                    continue  # сброс и новая итерация цикла

                # Имитация обработки: задержка 100-1000 мс
                await asyncio.sleep(random.uniform(0.1, 1.0))

                # Извлекаем номер запроса, т.е. цифру 0 из: "[0] PING" -> 0
                req_num: int = int(
                    message.split('[')[1].split(']')[0]
                )  # жоское место, последовательно разрезаем по ключевым символам
                response: str = (
                    f"[{self.response_counter}/{req_num}] PONG ({client_id})\n"
                )

                send_time: datetime.datetime = datetime.datetime.now()

                # Отправка ответа клиенту
                writer.write(response.encode(encoding="utf-8"))
                await writer.drain()

                # Логирование успешной обработки
                self.log_message(
                    message, receive_time, response.strip(), send_time
                )

                self.response_counter += 1

        except Exception:
            # Любая ошибка = разрыв соединения
            pass
        finally:
            # Очистка ресурсов при отключении клиента
            del self.clients[writer]
            writer.close()

    def log_ignored(
        self, message: str, receive_time: datetime.datetime
    ) -> None:
        """
        Логирует игнорированные сообщения в формате CSV.

        Формат записи:
            ГГГГ-ММ-ДД;ЧЧ:ММ:СС.ммм;запрос;(проигнорировано)

        Пример:
            2024-01-15;14:30:25.123;[0] PING;(проигнорировано)

        Args:
            message: str - текст запроса от клиента (например, "[0] PING")
            receive_time: datetime.datetime - время получения запроса
        """
        date_str: str = datetime.datetime.now().strftime('%Y-%m-%d')
        time_str: str = receive_time.strftime('%H:%M:%S.%f')[:-3]
        with open('server.log', 'a', encoding='UTF-8') as f:
            f.write(f"{date_str};{time_str};{message};(проигнорировано)\n")

    def log_message(
        self,
        message: str,
        receive_time: datetime.datetime,
        response: str,
        send_time: datetime.datetime,
    ) -> None:
        """
        Логирует успешно обработанные сообщения в формате CSV.

        Формат записи:
            ГГГГ-ММ-ДД;ЧЧ:ММ:СС.ммм_получения;запрос;ЧЧ:ММ:СС.ммм_отправки;ответ

        Пример:
            2024-01-15;14:30:25.123;[0] PING;14:30:25.567;[0/0] PONG (1)

        Args:
            message: str - текст запроса от клиента
            receive_time: datetime.datetime - время получения запроса
            response: str - текст ответа сервера
            send_time: datetime.datetime - время отправки ответа
        """
        date_str: str = datetime.datetime.now().strftime('%Y-%m-%d')
        recv_str: str = receive_time.strftime('%H:%M:%S.%f')[:-3]
        send_str: str = send_time.strftime('%H:%M:%S.%f')[:-3]
        with open('server.log', 'a', encoding='UTF-8') as f:
            f.write(f"{date_str};{recv_str};{message};{send_str};{response}\n")

    async def keepalive(self) -> None:
        """
        Периодическая отправка keepalive сообщений всем подключенным клиентам.

        Работает в бесконечном цикле:
        1. Ждет 5 секунд
        2. Формирует keepalive сообщение со сквозным номером
        3. Отправляет всем подключенным клиентам
        4. Увеличивает счетчик ответов

        Формат keepalive:
            [номер] keepalive\\n

        Пример:
            [5] keepalive\\n
        """
        while True:
            await asyncio.sleep(5)

            # Формируем keepalive сообщение
            keepalive_msg: str = f"[{self.response_counter}] keepalive\n"

            # Отправляем всем подключенным клиентам (список из ключей словаря)
            for writer in list(self.clients.keys()):
                try:
                    writer.write(keepalive_msg.encode(encoding="utf-8"))
                    await writer.drain()
                except:
                    # Клиент отключился, продолжаем с остальными, т.е. поглотили исключение
                    pass

            self.response_counter += 1

    async def start(self) -> None:
        """
        Запускает TCP-сервер и начинает принимать подключения.

        Процесс запуска:
        1. Создает TCP-сервер на 127.0.0.1:8888
        2. Запускает фоновую задачу keepalive
        3. Начинает принимать подключения клиентов
        4. Для каждого клиента запускает handle_client() в отдельной корутине
        5. Работает до принудительной остановки (Ctrl+C)

        Использует asyncio.start_server() для создания асинхронного TCP-сервера.
        """
        # Создание TCP-сервера
        # (первый аргумент - функция обратного вызова, переменная без вызова сразу)
        server: asyncio.Server = await asyncio.start_server(
            self.handle_client, '127.0.0.1', 8888
        )

        # Запуск фоновой задачи keepalive
        asyncio.create_task(self.keepalive())

        # Запуск основного цикла сервера
        async with server:
            print("Сервер запущен на порту 8888")
            await server.serve_forever()


if __name__ == "__main__":
    """
    Точка входа для запуска сервера напрямую.

    При запуске скрипта напрямую:
    1. Очищается лог-файл server.log
    2. Создается экземпляр Server
    3. Запускается асинхронный цикл с server.start()
    4. Обрабатывается Ctrl+C для корректного завершения
    """
    # Очищаем лог файл при каждом запуске
    open('server.log', 'w').close()

    try:
        server: Server = Server()
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\nСервер остановлен")


# Если у нас одна коробка 11,5 руб, а коробок 1000, то мы бы получили 11500 руб.

# а так мы получим после дождя 10960 руб.

# Разница 540 руб.
