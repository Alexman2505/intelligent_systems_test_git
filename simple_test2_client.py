import socket


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', 8686))
sock.send('hello, world!'.encode('utf-8'))  # или b'hello, world!'
data = sock.recv(1024)
if data:
    print(f"Received: {data.decode('utf-8')}")
else:
    print("No data received")
sock.close()
print("Connection closed")
