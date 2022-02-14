import asyncio
import json

car_count_answer = None
traffic_control = None

async def _jsn(jsn):
    car_count_tmp = ""
    for key, value in jsn['traffic_count'].items():
        car_count_tmp += f"{key}:{value}|"
    global car_count_answer
    car_count_answer = car_count_tmp

async def _handler(reader, writer):
    data = await reader.read(1024)
    message = data.decode()
    addr = writer.get_extra_info('peername')

    print(f"Received {message!r} from {addr!r}")

    message = message.strip('\n')

    itendifier = message.split('|')[0].rstrip(' ')

    answer = ""

    if itendifier == "road_lines":
        jsn_tmp = json.loads("".join(message.split('|')[1:]))
        task = asyncio.create_task(_jsn(jsn_tmp))
        answer = "okey"

    elif itendifier == "car_count":
        if car_count_answer != None:
            answer = car_count_answer
        else:
            answer = "None"
    
    elif itendifier == "ctc":
        global traffic_control
        traffic_control = "".join(message.split('|')[1:])
    
    elif itendifier == "get_ctc":
        if traffic_control != None:
            answer = traffic_control
        else:
            answer = "None"

    print(f"Send: {answer!r}")

    writer.write(bytes(answer, encoding="UTF-8"))
    await writer.drain()

    print("Close the connection")
    writer.close()

async def main():
    server = await asyncio.start_server(_handler, '127.0.0.1', 8686)

    addr = server.sockets[0].getsockname()
    print(f"Serving on {addr}")

    async with server:
        await server.serve_forever()

asyncio.run(main())