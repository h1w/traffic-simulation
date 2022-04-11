import asyncio
import logging

logging.basicConfig(format='%(asctime)s %(lineno)d %(levelname)s:%(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Connected client records
clients = dict()

async def show_tasks():
  while True:
    await asyncio.sleep(5)
    logger.debug(asyncio.Task.all_tasks())

def client_connected_cb(client_reader, client_writer):
  # Use peername as client ID
  client_id = client_writer.get_extra_info('peername')

  logger.ingo(f'CLient connected: {client_id}')

  # Defind the clean up function here
  def client_cleanup(fu):
    logger.ingo(f'Cleaning up client {client_id}')
    try: # Retrievre the result and ignore whatever returned, since it's just cleaning
      fu.result()
    except Exception as e:
      pass
    # Remove the client from client records
    del clients[client_id]
  
  task = asyncio.ensure_future(client_task(client_reader, client_writer))
  task.add_done_callback(client_cleanup)
  # Add the client and the task to client records
  clients[client_id] = task

async def client_task(reader, writer):
  client_addr = writer.get_extra_info('peername')
  logger.info(f'Start echoing back to {client_addr}')

  while True:
    data = await reader.read(1024)
    if data == b'':
      logger.info('Received EOF. CLient disconnected.')
      return
    else:
      writer.write(data)
      await writer.drain()

if __name__ == '__main__':
  host = '0.0.0.0'
  port = 8000
  loop = asyncio.get_event_loop()
  server_coro = asyncio.start_server(client_connected_cb, host=host, port=port, loop=loop)
  server = loop.run_until_complete(server_coro)

  try:
    logger.info(f'Serving on {host}:{port}')
    loop.run_forever()
  except KeyboardInterrupt as e:
    logger.info('Keyboard interrupted. Exit.')
  
  # Close the server
  server.close()
  loop.run_until_complete(server.wait_closed())
  loop.close()