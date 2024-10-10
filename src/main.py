import os
import argparse
from dotenv import load_dotenv
load_dotenv()

from config import get_config
from utils.models.t2t import model_dict as T2TModelDict
from utils.models.tts import TTSAI
from jaison_bot import JAIsonBot

# Fetch config file
args = argparse.ArgumentParser()
args.add_argument('--config', required=True, type=str, help='Filepath to your json config. See configs/example.json for example.')
args = args.parse_args()
config = get_config(args.config)

# Select models based on configuration
t2t_worker = T2TModelDict[config['t2t_host']](**config)
tts_worker = TTSAI(**config)

# Create the bot
bot = JAIsonBot(t2t_worker, tts_worker)

# Start running
bot.run(os.getenv("DISCORD_BOT_TOKEN"))