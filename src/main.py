from dotenv import load_dotenv
from utils.args import args
load_dotenv(dotenv_path=args.env_file)

import asyncio
from threading import Thread
from utils.jaison import JAIson
from utils.signal import GracefulKiller
from utils.server import SocketServerObserver, start_rest_api

def main():
    jaison = JAIson()
    kill_handler = GracefulKiller()
    kill_handler.add_cleanup(jaison)

    rest_api_thread = Thread(target=asyncio.run, args=(start_rest_api(),), daemon=True)
    rest_api_thread.start()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    socket_server = SocketServerObserver()

    loop.run_until_complete(socket_server.socket_server)

    try:
        loop.run_forever()  # Keep the event loop running
    except KeyboardInterrupt:
        raise
    finally:
        loop.close()

if __name__=="__main__":
    main()