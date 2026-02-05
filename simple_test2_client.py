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
if __name__ == "__main__":
    client = SocketClient('localhost', 8686)
    print('client starting')

    try:
        client.send_text('Hello from client!')
        response = client.receive_text()
        print(f'Response 1: {response}')

        client.send_json({"cmd": "start", "msg": "starting"})
        response = client.receive_json()
        print(f'Response 2: {response}')

    except Exception as e:
        print(f'Error: {e}')
    finally:
        client.close()
