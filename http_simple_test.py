# simple_test.py
import socket

# Подключаемся
sock = socket.socket()
sock.connect(('localhost', 53210))

# Отправляем HTTP запрос
request = """GET /users HTTP/1.1
Host: example.local
Accept: application/json

"""

sock.send(request.encode())

# Получаем ответ
response = sock.recv(4096)
print(response.decode())

sock.close()
