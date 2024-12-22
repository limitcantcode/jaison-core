import os
from dotenv import load_dotenv
load_dotenv()
from utils.args import args
from utils.jaison import JAIson
from utils.discord import DiscordBot
from webui import start_ui
from threading import Thread

jaison_main = JAIson(init_config_file=args.config)

# For Discord Bot
discord_bot = DiscordBot(jaison_main)
discord_thread = Thread(target=discord_bot.run, args=[os.getenv("DISCORD_BOT_TOKEN")])
discord_thread.start()

# For Web UI
web_thread = Thread(target=start_ui, args=[jaison_main])
web_thread.start()

# Keep running this main thread while others threads are active
discord_thread.join()
web_thread.join()