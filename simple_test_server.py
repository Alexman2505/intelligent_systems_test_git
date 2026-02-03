import socket

# Сокет — это программный объект (интерфейс), представляющий конечную точку сетевого соединения,
# определяемую уникальной комбинацией IP-адреса, номера порта и транспортного протокола,
# предоставляющий интерфейс для отправки и получения данных через сеть.

# Задаем адрес сервера (комбинация 4 элементов):
# IP-адрес (куда/откуда)
# Номер порта (какому приложению)
# Транспортный протокол (TCP или UDP)
# Состояние соединения (если TCP)

# Приложение
#     ↓
# Библиотека сокетов (socket API)
#     ↓
# Транспортный уровень (TCP/UDP) ←→ Буферы ОС
#     ↓
# Сетевой уровень (IP)
#     ↓
# Канальный уровень (Ethernet/WiFi)
#     ↓
# Физический уровень (провода/радио)


server_socket = socket.socket(
    socket.AF_INET,  # IPv4 протокол (семейство адресов)
    socket.SOCK_STREAM,  # TCP протокол (тип сокета)
)
SERVER_ADDRESS = ('localhost', 8686)
server_socket.bind(SERVER_ADDRESS)
server_socket.listen(10)
print('server is running, please, press ctrl+c to stop')

# Слушаем запросы
while True:
    connection, address = server_socket.accept()
    print()
    print("new connection from {address}".format(address=address))
    data = connection.recv(1024)
    print(str(data))
    connection.send(bytes('Hello from server!', encoding='UTF-8'))
    connection.close()
