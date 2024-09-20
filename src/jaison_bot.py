'''
Bot containing all of J.A.I.son's functionality
'''

import discord
from cogs.cogs import setup_cogs
from .utils.models import BaseT2TAIWorker

class JAIsonBot(discord.Bot):

    def __init__(self, llm_worker: BaseT2TAIWorker):
        super().__init__(intents=discord.Intents.all())
        self.llm_worker = llm_worker
        setup_cogs(self)

    # handler for initially turning on
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    # handler for raw messages appearing in chat
    async def on_message(self, message):
        if self.application_id == message.author.id:
            return
    
        author = message.author.nick if message.author.nick is not None else message.author.global_name
        print(f'Message from {author}: {message.content}')
        response = self.llm_worker(message.content, author)
        print(f'Sending response: {response}')
        responses = [msg for msg in response.split('\\n') if len(msg)>0]
        if len(responses) == 0:
            responses = ['...']
        for msg in responses:
            await message.channel.send(msg)