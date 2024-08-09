from discord.ext import commands
import discord
import asyncio

from cogs.defaults import default_params

class NotInVCException(Exception):
    pass

class VoiceCog(commands.Cog):
    '''
    Add VC functionality for bots
    '''

    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot
        self.vc = None

    def _check_connected(self) -> bool:
        '''Return whether bot is connected to a vc'''
        return self.vc is not None and self.vc.is_connected()
    
    async def _disconnect_client_if_connected(self) -> bool:
        '''Disconnect bot from vc if in one and return whether bot performed a dc or not'''
        if self._check_connected():
            await self.vc.disconnect()
            return True
        else:
            return False

    @discord.slash_command(description="Join a voice channel.", name="join_vc", **default_params)
    @discord.option("channel", type=discord.channel.VoiceChannel)
    async def join_vc(self, ctx, channel: discord.VoiceChannel) -> None:
        '''Join bot to specified vc'''
        try:
            await self._disconnect_client_if_connected() # bot cannot connect if it is already in a vc
            self.vc = await channel.connect()
            await ctx.respond(f"Joined {channel}!")
        except discord.ClientException as err:
            print(err)
            await ctx.respond(f"Failed to change channels to {channel}. Try again...")
            return
        except asyncio.TimeoutError as err:
            print(err)
            await ctx.respond(f"Request to join {channel} timed out. Try again...")
            return
        except Exception as err:
            print(err)
            await ctx.respond(f"Failed to join {channel}...")
            return

    @discord.slash_command(description="Leave current voice channel.", name="leave_vc", **default_params)
    async def leave_vc(self, ctx) -> None:
        '''Disconnect bot from current vc'''
        try:
            if not await self._disconnect_client_if_connected():
                raise NotInVCException()
            await ctx.respond(f"Left voice channel")
        except NotInVCException as err:
            print(err)
            await ctx.respond(f"Not in a voice channel..")
            return
        except Exception as err:
            print(err)
            await ctx.respond(f"Failed to leave current voice channel...")
            return

    @discord.slash_command(description="Play a sound.", name="play_sound", **default_params)
    async def play_sound(self, ctx) -> None:
        '''Play a preset sound in current vc'''
        try:
            if not self._check_connected():
                raise NotInVCException()
            source = discord.FFmpegPCMAudio('D:\\Projects\\LCC\\jaison\\src\\assets\\Baba Booey - Sound Effect (HD).ogg')
            await self.vc.play(source, wait_finish=True)
            await ctx.respond(f"Played sound in current channel!")
        except NotInVCException as err:
            print(err)
            await ctx.respond(f"Not in a voice channel. Please have me join a voice channel to play into...")
            return
        except Exception as err:
            print(err)
            await ctx.respond(f"Failed to play sound in current channel...")
            return
        
    async def _record_callback(self, sink: discord.sinks.Sink) -> None:
        '''
        Store audio from sink into one audio file per user
        
        NOTE: Will be triggered automatically upon stopping recording
        '''
        
        audio_data = sink.get_all_audio()
        for buffer_ind in range(len(audio_data)):
            with open(f"recordings/{buffer_ind}.mp3", "wb") as f: # store audio files in root/recordings directory. File indexed by user
                f.write(audio_data[buffer_ind].getbuffer())

        
    @discord.slash_command(description="Start recording current voice channel audio.", name="record_start", **default_params)
    async def record_start(self, ctx) -> None:
        '''Start recording audio per user in current vc'''
        try:
            if not self._check_connected():
                raise NotInVCException()
            sink = discord.sinks.MP3Sink()
            self.vc.start_recording(sink, self._record_callback, sync_start=True)
            await ctx.respond(f"Started recording!")
        except NotInVCException as err:
            print(err)
            await ctx.respond(f"Not in a voice channel. Please have me join a voice channel to play into...")
            return
        except discord.sinks.RecordingException as err:
            print(err)
            await ctx.respond(f"Already recording...")
        except Exception as err:
            print(err)
            await ctx.respond(f"Failed to start recording...")
            return
        
    @discord.slash_command(description="Stop recording current voice channel audio.", name="record_stop", **default_params)
    async def record_stop(self, ctx) -> None:
        '''Stop recording audio in current vc'''
        try:
            if not self._check_connected():
                raise NotInVCException()
            self.vc.stop_recording()
            await ctx.respond(f"Stopped recording!")
        except NotInVCException as err:
            print(err)
            await ctx.respond(f"Not in a voice channel. Please have me join a voice channel to play into...")
            return
        except discord.sinks.RecordingException as err:
            print(err)
            await ctx.respond(f"Was not even recording...")
            return
        except Exception as err:
            print(err)
            await ctx.respond(f"Failed to stop recording...")
            return

'''Augment inputted bot with this cog'''
def setup(bot: discord.Bot) -> None:
    bot.add_cog(VoiceCog(bot))