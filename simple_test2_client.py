import socket


client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('localhost', 8686))
client_socket.send(
    'Hello from client'.encode('utf-8')
)  # или b'Hello' Это 5 байт: [72, 101, 108, 108, 111]
data = client_socket.recv(1024)
print(f"Received: {data.decode('utf-8')}")
client_socket.close()
print("Connection closed")
