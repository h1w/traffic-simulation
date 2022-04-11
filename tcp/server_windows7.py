import asyncio, socket
import json
import threading
import time
import logging

logging.basicConfig(format='%(asctime)s %(lineno)d %(levelname)s:%(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Connected client records
clients = dict()

server_addr = '0.0.0.0'
server_port = 8000
car_count_answer = None
traffic_control = None

async def TrafficControl():
  # Прочитать данные из файла
  data = ''
  # Отправить данные на сервер
  

async def handle_client(reader, writer):
  # Если это первый клиент, запустить асинхронную задачу с постоянной отправкой данных на windows7 сервер
  
  # Принимать остальные запросы
  request = None
  addr = writer.get_extra_info('peername')
  while request != 'quit':
    request = (await reader.read(1024)).decode('utf8')

    response = 'Accepted'
    writer.write(response.encode('utf8'))
    await writer.drain()

async def run_server():
  server = await asyncio.start_server(handle_client, server_addr, server_port)
  async with server:
    await server.serve_forever()
  
asyncio.run(run_server())