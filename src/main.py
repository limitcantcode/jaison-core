import os
from dotenv import load_dotenv
load_dotenv()

from utils.args import args
from utils.models.t2t import model_dict as T2TModelDict, get_prompt_from_file
from jaison_bot import JAIsonBot


llm_worker = T2TModelDict[args.t2t_ai](
    get_prompt_from_file(args.prompt_file),
    **args
)
bot = JAIsonBot(llm_worker)

bot.run(os.getenv("DISCORD_BOT_TOKEN"))