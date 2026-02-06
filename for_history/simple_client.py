import socket


def start_tcp_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 12345))  # Подключаемся к серверу

    message = "Привет, сервер!".encode()  # Преобразуем строку в байты
    client_socket.sendall(message)  # Отправляем сообщение

    response = client_socket.recv(1024)  # Получаем ответ
    print(f"Ответ сервера: {response.decode()}")

    client_socket.close()  # Закрываем соединение


##################################################
# def start_udp_client():
#     sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#     message = "Привет, UDP-сервер!".encode()
#     sock.sendto(message, ('localhost', 12345))  # Отправляем сообщение

#     response, _ = sock.recvfrom(1024)  # Получаем ответ
#     print(f"Ответ сервера: {response.decode()}")

#     sock.close()


# start_udp_client()
