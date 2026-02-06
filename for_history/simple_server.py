import socket


def start_tcp_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 12345))  # Привязываем к адресу и порту
    server_socket.listen(1)  # Начинаем слушать (1 - макс. очередь подключений)

    print("Сервер запущен и ожидает подключений...")

    while True:
        client_socket, addr = server_socket.accept()  # Принимаем подключение
        print(f"Подключен клиент: {addr}")

        data = client_socket.recv(1024)  # Получаем данные (макс. 1024 байт)
        print(f"Получено: {data.decode()}")

        client_socket.sendall(data)  # Отправляем данные обратно
        client_socket.close()  # Закрываем соединение


# start_tcp_server()

######################################
# def start_udp_server():
#     sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     sock.bind(('localhost', 12345))

#     print("UDP-сервер запущен...")

#     while True:
#         data, addr = sock.recvfrom(1024)  # Получаем данные и адрес отправителя
#         print(f"Получено от {addr}: {data.decode()}")
#         sock.sendto(data, addr)  # Отправляем ответ обратно


# start_udp_server()
