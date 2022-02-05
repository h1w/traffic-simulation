import socket
import time

address_to_server = ('localhost', 8686)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(address_to_server)

while True:
    client.send(bytes("hello from client", encoding='UTF-8'))

    data = client.recv(1024)
    print(str(data))

    time.sleep(1)