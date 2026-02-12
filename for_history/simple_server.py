import socket

URLS = {'/': 'hello index', '/blog': 'hello blog'}


def parse_request(request):
    parsed = request.split(' ')
    method = parsed[0]
    url = parsed[1]
    return (method, url)


def generate_headers(method, url):
    if not method == 'GET':
        return ('HTTP/1.1 405 Method not allowed\n', 405)

    if not url in URLS:
        return ('HTTP/1.1 404 Method not found\n', 404)
    return ('HTTP/1.1 200 OK\n\n', 200)


def generate_content(code, url):
    if code == 404:
        return '<h1>404</h1><p>Not found</p>'
    if code == 405:
        return '<h1>405</h1><p>Method not allowed</p>'
    return '<h1>{}</h1>'.format(URLS[url])


def generate_response(request):
    method, url = parse_request(request)
    headers, code = generate_headers(method, url)
    body = generate_content(code, url)
    return (headers + body).encode(encoding='utf-8')


def start_tcp_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 12345))  # Привязываем к адресу и порту
    server_socket.listen(1)  # Начинаем слушать (1 - макс. очередь подключений)
    print("Сервер запущен и ожидает подключений...")

    while True:
        client_socket, addr = server_socket.accept()  # Принимаем подключение
        print(f"Подключен клиент: {addr}")

        request = client_socket.recv(1024)  # Получаем данные (макс. 1024 байт)
        print(f"Получено: {request.decode(encoding='utf-8')}")

        if not request:
            print(
                '-----------------------------------------------------------------'
            )
            print("Получен пустой запрос, закрываем соединение")
            print(
                '-----------------------------------------------------------------'
            )
            client_socket.close()
            continue  # Пропускаем итерацию

        response = generate_response(request.decode(encoding='utf-8'))
        client_socket.sendall(response)  # Отправляем данные обратно
        print('-------------------')
        print(f"Это ответ response {response}")
        print(
            '-----------------------------------------------------------------'
        )
        print()
        print()
        print()
        print()
        client_socket.close()  # Закрываем соединение


if __name__ == '__main__':
    start_tcp_server()

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
