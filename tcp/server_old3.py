import asyncio, socket
import json
import threading
import time

server_addr = '0.0.0.0'
server_port = 8000

car_count_answer = None
traffic_control = None

async def _jsn(jsn):
    car_count_tmp = ''
    for key, value in jsn['traffic_count'].items():
        car_count_tmp += f'/{value}*'
    global car_count_answer
    car_count_answer = car_count_tmp

async def TrafficControl(request):
    traffic_control_tmp = ''
    # /A1:g*/A2:r*/A3:r*/A4:g*/A6:g*/A7:r*
    l = request.split('/')[1:]
    for i in l:
        key = i.split(':')[0]
        value = i.split(':')[1].rstrip('*')
        if value == 'r':
            value = 'red'
        elif value == 'g':
            value = 'green'
        traffic_control_tmp += f'|{key}:{value}'
    global traffic_control
    traffic_control = ''.join(traffic_control_tmp.split('|')[1:])

send_traffic_info_alive = True
thread_writer = None
async def SendTrafficInfo():
    global thread_writer
    print('Send traffic info has been started')
    while send_traffic_info_alive:
        try:
            response = 'None'
            if car_count_answer != None:
                response = car_count_answer
            thread_writer.write(response.encode('utf8'))
            await thread_writer.drain()
            print('request has been received to windows7 machine in thread')
            time.sleep(3)
        except Exception as e:
            pass

# send_traffic_info_thread = threading.Thread(target=SendTrafficInfo, args=(thread_writer,))

clients = {
    'raspberry': None,
    'windows7': None,
}

async def handle_client(reader, writer):
    print('NEW CLIENT', reader, writer, writer.get_extra_info('peername'))
    global clients
    request = None
    addr = writer.get_extra_info('peername')
    while request != 'quit':
        if clients['raspberry'] == None or clients['windows7'] == None:
            request = (await reader.read(1023)).decode('utf8')
            print(f'Received {request!r} from {addr!r}')

            if request != None:
                if request == 'raspberry':
                    clients['raspberry'] = writer
                    print('raspberry pi has been connected', writer)
                else:
                    global thread_writer
                    global send_traffic_info_thread
                    trehad_writer = writer
                    clients['windows7'] = writer
                    print('windows 7 has been connected', writer)
                    task = asyncio.create_task(SendTrafficInfo())
                    print('send traffic info thread has been started')
        
        if clients['raspberry'] != None and addr == clients['raspberry'].get_extra_info('peername'):
            # Логика для малинки
            request = (await reader.read(1023)).decode('utf8')
            print(f'Received {request!r} from {addr!r} raspberry')

            task = asyncio.create_task(_jsn(json.loads(request)))

            response = 'Accepted'
            writer.write(response.encode('utf8'))
            await writer.drain()
            print(f'Sended {response!r} to {addr!r} raspberry')
            # Обработать запрос от малинки по светофорам
        elif clients['windows7'] != None and addr == clients['windows7'].get_extra_info('peername'):
            # Логика для управляющего сервера на винде Елькина
            # Жестко получить от управляющего сервера значение светофоров
            # и отправить ответ на малинку

            request = (await reader.read(1023)).decode('utf8')
            print(f'Received {request!r} from {addr!r} Windows7')

            # Откликнуться серверу
            response = 'Accepted'
            writer.write(response.encode('utf8'))
            await writer.drain()
            print(f'Sended {response!r} to {addr!r} Windows7')

            # Отправить запрос на малину, с указанием включения светофоров
            global traffic_control
            response = traffic_control
            clients['windows7'].write(response.encode('utf8'))
            await clients['windows7'].drain()
            print(f'Sended {response!r} to {addr!r} (raspberry)')
    writer.close()

async def run_server():
    server = await asyncio.start_server(handle_client, server_addr, server_port)
    async with server:
        await server.serve_forever()

asyncio.run(run_server())