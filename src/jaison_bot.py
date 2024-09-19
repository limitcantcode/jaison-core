'''
Bot containing all of J.A.I.son's functionality
'''

import discord
from cogs.cogs import setup_cogs

class JAIsonBot(discord.Bot):

    def __init__(self, llm_worker):
        super().__init__(intents=discord.Intents.all())
        self.llm_worker = llm_worker
        setup_cogs(self)

    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        if self.application_id == message.author.id:
            return
    
        author = message.author.nick if message.author.nick is not None else message.author.global_name
        print(f'Message from {author}: {message.content}')
        response = self.llm_worker(message.content, author)
        print(f'Sending response: {response}')

        await message.channel.send(response)