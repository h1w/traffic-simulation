import asyncio
import json
import threading

server_addr = '127.0.0.1'
server_port = 8686

send_traffic_info_alive = True
thread_writer = None
def SendTrafficInfo(thead_writer):
    print('Send traffic info has been started')
    while send_traffic_info_alive:
        pass

send_traffic_info_thread = threading.Thread(target=SendTrafficInfo, args=(thread_writer,))

ok = True
async def _handler(reader, writer):
    data = await reader.read(1024)
    message = data.decode()
    addr = writer.get_extra_info('peername')

    print(f'Received {message!r} from {addr!r}')

    if ok:
        thread_writer = writer
        send_traffic_info_thread.start()
        ok = False

    answer = "test answer"

    print(f'Send: {answer!r}')

    writer.write(bytes(answer, encoding='UTF-8'))
    await writer.drain()

    print('Close the connection')
    writer.close()

async def main():
    server = await asyncio.start_server(_handler, server_addr, server_port)
    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')

    async with server:
        await server.serve_forever()

asyncio.run(main())