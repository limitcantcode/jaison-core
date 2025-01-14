import os
from dotenv import load_dotenv
load_dotenv()
import time
from utils.args import args
from utils.jaison import JAIson
from utils.discord import DiscordBot
from utils.signal import GracefulKiller
from webui import start_ui
from threading import Thread

jaison_main = JAIson()
kill_handler = GracefulKiller(jaison_main)
jaison_main.setup(init_config_file=args.config)

# For Discord Bot
discord_bot = DiscordBot(jaison_main)
discord_thread = Thread(target=discord_bot.run, args=[os.getenv("DISCORD_BOT_TOKEN")], daemon=True)
discord_thread.start()

# For Web UI
web_thread = Thread(target=start_ui, args=[jaison_main], daemon=True)
web_thread.start()

# Keep running this main thread while others threads are active
# Don't ever join threads that run forever otherwise can't exit on kill signals
# Slow polling busy wait is scuffed, ik but it works
while True:
    time.sleep(5)