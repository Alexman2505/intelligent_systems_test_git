import subprocess
import time
import os
import sys
from pathlib import Path


def clear_logs():
    """Очищаем старые логи"""
    log_files = ['server.log', 'client_1.log', 'client_2.log']
    for filename in log_files:
        if os.path.exists(filename):
            os.remove(filename)


def main():
    """Запускаем сервер и двух клиентов"""

    # Получаем путь к текущей папке, где лежат скрипты
    current_dir = os.path.dirname(os.path.abspath(__file__))

    print(f"Текущая папка: {current_dir}")

    print("Очищаем старые логи...")
    clear_logs()

    print("Запускаем сервер...")
    # Запускаем сервер из текущей папки
    server = subprocess.Popen(
        [sys.executable, os.path.join(current_dir, 'server.py')],
        cwd=current_dir,  # Указываем рабочую директорию
    )

    # Ждем запуска сервера
    time.sleep(2)

    print("Запускаем клиента 1...")
    client1 = subprocess.Popen(
        [sys.executable, os.path.join(current_dir, 'client.py'), '1'],
        cwd=current_dir,
    )

    time.sleep(0.5)

    print("Запускаем клиента 2...")
    client2 = subprocess.Popen(
        [sys.executable, os.path.join(current_dir, 'client.py'), '2'],
        cwd=current_dir,
    )

    print("\nВсе запущено! Работаем 5 минут...")
    print("(Нажмите Ctrl+C чтобы остановить досрочно)")

    try:
        # Ждем 5 минут (300 секунд)
        time.sleep(300)
    except KeyboardInterrupt:
        print("\nОстановка по команде пользователя...")

    print("Останавливаем процессы...")

    # Останавливаем клиентов
    client1.terminate()
    client2.terminate()
    client1.wait(timeout=5)
    client2.wait(timeout=5)

    # Останавливаем сервер
    server.terminate()
    server.wait(timeout=5)

    print("\nГотово! Логи сохранены в текущей папке:")
    for log_file in ['server.log', 'client_1.log', 'client_2.log']:
        if os.path.exists(os.path.join(current_dir, log_file)):
            print(f"- {log_file}")


if __name__ == "__main__":
    main()
