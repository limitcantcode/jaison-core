'''
Bot containing all of J.A.I.son's functionality
'''

import discord
from cogs.cogs import setup_cogs
from utils.models.t2t import BaseT2TAIWorker
from utils.models.tts import TTSAI

class JAIsonBot(discord.Bot):

    def __init__(self, t2t_worker: BaseT2TAIWorker, tts_worker: TTSAI):
        super().__init__(intents=discord.Intents.all())
        self.t2t_worker = t2t_worker
        self.tts_worker = tts_worker
        self.vc = None

        setup_cogs(self)

    # handler for initially turning on
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    # handler for raw messages appearing in chat
    # will speak response if in a vc
    async def on_message(self, message):
        # Skip messages from self
        if self.application_id == message.author.id:
            return

        # Show typing indicator
        await message.channel.trigger_typing()

        # Get response
        author = message.author.nick if message.author.nick is not None else message.author.global_name
        print(f'Message from {author}: {message.content}')
        response = self.t2t_worker(message.content, author)
        print(f'Sending response: {response}')
        responses = [msg for msg in response.split('\\n') if len(msg)>0]

        # Respond in text chat
        if len(responses) == 0:
            responses = ['...']
        for msg in responses:
            await message.channel.send(msg)

        # Speak in VC if applicable
        if self.vc is not None and self.vc.is_connected():
            try:
                audio_file = self.tts_worker(msg)
                source = discord.FFmpegPCMAudio(audio_file)
                await self.vc.play(source, wait_finish=True)
            except Exception as err:
                print(f"Error occured while playing TTS in response to text: {err}")