import os
from dotenv import load_dotenv
load_dotenv()

from jaison_bot import JAIsonBot

bot = JAIsonBot()
bot.run(os.getenv("DISCORD_BOT_TOKEN"))