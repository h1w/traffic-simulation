import socket

address_to_server = ('localhost', 8686)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(address_to_server)

# msg = """
# road_lines | {"traffic_count": {"A1": 8, "A2": 7, "A3": 1, "A4": 0, "A5": 4, "A6": 3, "A7": 0, "A8": 2, "A9": 7, "A10": 7, "A11": 0, "A12": 0, "A13": 0, "A14": 0, "A15": 1, "A16": 3, "A17": 0, "A18": 12, "A19": 6, "A20": 2, "A21": 2, "A22": 2, "A23": 0, "A24": 3, "A25": 0, "A26": 0, "A27": 2, "A28": 8, "A29": 6, "A30": 13}}
# """

msg = """
car_count
"""

client.send(bytes(msg, encoding="UTF-8"))

data = client.recv(1024)

print(str(data))