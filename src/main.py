import os
from dotenv import load_dotenv
load_dotenv()

from config import config
from utils.models.t2t import model_dict as T2TModelDict
from utils.models.tts import TTSAI
from jaison_bot import JAIsonBot

# Select models based on configuration
t2t_worker = T2TModelDict[config['t2t_host']]()
tts_worker = TTSAI()

# Create the bot
bot = JAIsonBot(t2t_worker, tts_worker)

# Start running
bot.run(os.getenv("DISCORD_BOT_TOKEN"))