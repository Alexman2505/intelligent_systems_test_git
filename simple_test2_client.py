# import socket


# client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# client_socket.connect(('localhost', 8686))
# client_socket.send(
#     'Hello from client'.encode('utf-8')
# )  # или b'Hello' Это 5 байт: [72, 101, 108, 108, 111]
# data = client_socket.recv(1024)
# print(f"Received: {data.decode('utf-8')}")
# client_socket.close()
# print("Connection closed")

import socket
import time
import json


class SocketClient:
    ENCODING = 'utf-8'

    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))

    def send_text(self, text):
        """Отправляет текст"""
        data = text.encode(self.ENCODING)
        self.sock.send(data)

    def send_json(self, data):
        """Отправляет JSON"""

        json_str = json.dumps(data, ensure_ascii=False)
        self.send_text(json_str)

    def receive_text(self, buffer_size=1024):
        """Получает текст"""
        data = self.sock.recv(buffer_size)
        return data.decode(self.ENCODING)

    def receive_json(self):
        """Получает JSON"""
        text = self.receive_text()
        return json.loads(text)

    def close(self):
        self.sock.close()


# Использование
client = SocketClient('localhost', 8686)
client.send_text('Hello, server!')
response = client.receive_text()
print(response)

client.send_json({"cmd": "start", "msg": "starting"})
response = client.receive_json()
print(response)
client.close()
