# import socket


# def start_tcp_server():
#     server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     server_socket.bind(('localhost', 12345))  # Привязываем к адресу и порту
#     server_socket.listen(1)  # Начинаем слушать (1 - макс. очередь подключений)

#     print("Сервер запущен и ожидает подключений...")

#     while True:
#         client_socket, addr = server_socket.accept()  # Принимаем подключение
#         print(f"Подключен клиент: {addr}")

#         data = client_socket.recv(1024)  # Получаем данные (макс. 1024 байт)
#         print(f"Получено: {data.decode()}")

#         client_socket.sendall(data)  # Отправляем данные обратно
#         client_socket.close()  # Закрываем соединение


# start_tcp_server()


# def start_udp_server():
#     sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     sock.bind(('localhost', 12345))

#     print("UDP-сервер запущен...")

#     while True:
#         data, addr = sock.recvfrom(1024)  # Получаем данные и адрес отправителя
#         print(f"Получено от {addr}: {data.decode()}")
#         sock.sendto(data, addr)  # Отправляем ответ обратно


# start_udp_server()

import socket
import json


class SocketServer:
    ENCODING = 'utf-8'

    def __init__(self, host='0.0.0.0', port=8686):
        self.host = host
        self.port = port
        self.server_socket = None
        self.client_socket = None
        self.client_address = None

    def start(self):
        """Запускает сервер"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(10)
        print(f'Server listening on {self.host}:{self.port}...')

    def accept_client(self):
        """Принимает подключение клиента"""
        self.client_socket, self.client_address = self.server_socket.accept()
        print(f'\nClient connected from {self.client_address}')
        # return self.client_socket, self.client_address

    def receive_text(self, buffer_size=1024):
        """Получает текст от клиента"""
        if not self.client_socket:
            raise RuntimeError("No client connected")

        data = self.client_socket.recv(buffer_size)
        if not data:
            return None
        return data.decode(self.ENCODING)

    def receive_json(self):
        """Получает JSON от клиента"""
        text = self.receive_text()
        if text:
            return json.loads(text)
        return None

    def send_text(self, text):
        """Отправляет текст клиенту"""
        if not self.client_socket:
            raise RuntimeError("No client connected")

        data = text.encode(self.ENCODING)
        self.client_socket.send(data)

    def send_json(self, data):
        """Отправляет JSON клиенту"""
        json_str = json.dumps(data, ensure_ascii=False)
        self.send_text(json_str)

    def close_client(self):
        """Закрывает соединение с клиентом"""
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
            print(f'Connection with {self.client_address} closed')

    def close_server(self):
        """Завершает работу сервера"""
        self.close_client()
        if self.server_socket:
            self.server_socket.close()
            print('Server stopped')


# Использование сервера
if __name__ == "__main__":
    server = SocketServer('0.0.0.0', 8686)
    server.start()

    try:
        while True:
            # Ждем клиента
            server.accept_client()

            # Общаемся с клиентом
            while True:
                # Получаем сообщение
                message = server.receive_text()
                if not message:  # Клиент отключился
                    break

                print(f'From client: {message}')

                # Отправляем ответ
                server.send_text(message)

            # Закрываем соединение с этим клиентом
            server.close_client()

    except KeyboardInterrupt:
        print('\nServer stopped by user')
    finally:
        server.close_server()
