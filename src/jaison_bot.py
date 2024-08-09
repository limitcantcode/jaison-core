'''
Bot containing all of J.A.I.son's functionality
'''

import discord
from utils.service.openai_worker import OpenAIWorker
from cogs.cogs import setup_cogs

class JAIsonBot(discord.Bot):

    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.llm_worker = OpenAIWorker()
        setup_cogs(self)

    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        if self.application_id == message.author.id:
            return
    
        print(f'Message from {message.author}: {message.content}')
        response = self.llm_worker.get_response(message.content)
        print(f'Sending response: {response}')

        await message.channel.send(response)