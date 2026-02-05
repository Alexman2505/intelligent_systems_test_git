import socket
import time
import json

# Сокет — это программный объект (интерфейс), представляющий
# конечную точку сетевого соединения, определяемую уникальной комбинацией
#  IP-адреса, номера порта и транспортного протокола,
# предоставляющий интерфейс для отправки и получения данных через сеть.


# Приложение
# Библиотека сокетов (socket API)
# Транспортный уровень (TCP/UDP) TCP сегменты
# Сетевой уровень (IP) IP пакеты
# Канальный уровень (Ethernet/WiFi) Ethernet фреймы
# Физический уровень (провода/радио) Электрические/оптические сигналы


def handle_client(client_socket, client_address):
    print(f"\nClient connected: {client_address}")

    while True:
        try:
            # Ждем данные от клиента
            data = client_socket.recv(1024)
            if not data:  # Клиент закрыл соединение
                print(f"Client {client_address} disconnected")
                break

            # Пытаемся понять, что пришло
            try:
                text = data.decode('utf-8')

                # Пробуем распарсить как JSON
                try:
                    json_data = json.loads(text)
                    print(f"JSON from {client_address}: {json_data}")
                    response = {"status": "processed", "data": json_data}
                    client_socket.send(json.dumps(response).encode('utf-8'))
                except json.JSONDecodeError:
                    # Это просто текст
                    print(f"Text from {client_address}: {text}")
                    client_socket.send(f"Echo: {text}".encode('utf-8'))

            except UnicodeDecodeError:
                # Бинарные данные
                print(f"Binary data from {client_address}, size: {len(data)}")
                client_socket.send(b"Binary received")

        except ConnectionResetError:
            print(f"Client {client_address} disconnected abruptly")
            break
        except Exception as e:
            print(f"Error with {client_address}: {e}")
            break

    client_socket.close()
    print(f"Connection closed")


# Основной сервер
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('0.0.0.0', 8686))
server.listen(10)
print('Server listening on port 8686...')

while True:
    client_socket, client_address = server.accept()
    handle_client(client_socket, client_address)
