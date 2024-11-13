from discord.ext import commands, voice_recv
import discord
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import datetime
import wave
from .base import BaseCommandGroup
from utils.models.stt.stt_worker import STTWorker
from config import config

stt = STTWorker()

# Grouping of slash commands into a command list
class VoiceCommandGroup(BaseCommandGroup):
    def __init__(self, params={}):
        super().__init__(params)

        self.command_list = [
            join_vc,
            leave_vc
        ]

'''
Custom audio sink for managing call audio and triggering callback during silence.
This sink will save all recorded audio to buffer in memory. This buffer can be read
directly from this class at any time. Audio buffer will not be truncated until freshen(idx)
is called, to which all data up to and including idx will be truncated.
Audio is tracked per user in the call in the dictionary buf.
'''
class BufferSink(voice_recv.AudioSink):
    # Requires a callback function <fun(buf: BufferSink)> that will be called during silence
    # Callback accepts one arguement, and that is this BufferSink instance
    def __init__(self, stale_callback):
        self.buf = {}
        self.sample_width = 2
        self.sample_rate = 96000
        self.bytes_ps = 192000

        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
        self.stale_timer = None
        self.stale_callback = stale_callback

    def wants_opus(self):
        return False

	# just append data to the byte array
    def write(self, user, data):
        self.stale_timer = self.scheduler.add_job(
            self.stale_callback,
            'date',
            run_date=datetime.datetime.now()+datetime.timedelta(seconds=1),
            args=[self],
            id='vc_buffer_timer',
            replace_existing=True
        )
        if user.display_name not in self.buf:
            self.buf[user.display_name] = bytearray()
        self.buf[user.display_name] += data.pcm

    def freshen(self, idx, username):
        self.buf[username] = self.buf[username][idx:]

    def cleanup(self):
        pass


def _check_connected(client: discord.Client) -> bool:
    '''Return whether client is connected to a vc'''
    return client.vc is not None and client.vc.is_connected()

async def _disconnect_client_if_connected(client: discord.Client) -> bool:
    '''Disconnect client from vc if in one and return whether client performed a dc or not'''
    if _check_connected(client):
        client.vc.stop()
        await client.vc.disconnect()
        client.vc = None
        return True
    else:
        return False

'''
Client will join the specified VC. Client will start to listen to members of the call
and respond to what they are saying when there is silence.
'''
@discord.app_commands.command(name="join_vc", description="Join a voice channel.")
async def join_vc(interaction, channel: discord.VoiceChannel) -> None:
    async def vc_callback(buf: BufferSink):
        return await vc_reply(interaction.client, buf, interaction.channel)
    audio_buffer = BufferSink(vc_callback)

    try:
        await _disconnect_client_if_connected(interaction.client) # client cannot connect if it is already in a vc
        interaction.client.vc = await channel.connect(cls=voice_recv.VoiceRecvClient)
        interaction.client.vc.listen(audio_buffer)
        await interaction.response.send_message(f"Joined {channel}.")
    except discord.ClientException as err:
        print(err)
        await interaction.response.send_message(f"Failed to change channels to {channel}. Try again...")
        return
    except asyncio.TimeoutError as err:
        print(err)
        await interaction.response.send_message(f"Request to join {channel} timed out. Try again...")
        return
    except Exception as err:
        print(err)
        await interaction.response.send_message(f"Failed to join {channel}...")
        return

@discord.app_commands.command(description="Leave current voice channel.", name="leave_vc")
async def leave_vc(interaction) -> None:
    '''Disconnect client from current vc'''
    try:
        if not await _disconnect_client_if_connected(interaction.client):
            raise NotInVCException()
        await interaction.response.send_message(f"Left voice channel")
    except NotInVCException as err:
        print(err)
        await interaction.response.send_message(f"Not in a voice channel..")
        return
    except Exception as err:
        print(err)
        await interaction.response.send_message(f"Failed to leave current voice channel...")
        return

# Handler for speech pipeline
async def vc_reply(client: discord.Client, sink: BufferSink, called_channel: discord.abc.GuildChannel):
    global stt
    for username in sink.buf:
        # Obtain current audio buffer
        idx = len(sink.buf[username])
        curr_buff = sink.buf[username][:idx]

        # Open, configure, and write to file the current audio buffer
        f_path = config['stt_output_filepath']
        f = wave.open(f_path, 'wb')
        f.setnchannels(sink.sample_width)
        f.setsampwidth(sink.sample_width)
        f.setframerate(sink.sample_rate)
        f.writeframes(curr_buff)
        f.close()

        # Transcribe new file
        trans_script = stt(f_path)
        
        # Send transcription as input to T2T AI and get response
        response = client.t2t_worker(trans_script, username, retain_on_silence=False)
        print(response) # debug
        if response == '<no response>': # enable option for silence to continue listening for complete input
            return
        responses = [msg for msg in response.split('\\n') if len(msg)>0]
        speech_response = ''
        if len(responses) == 0:
            responses = ['...']
        for msg in responses:
            await called_channel.send(msg)
            speech_response += msg

        # If a response is received and to be outputted, clear processed bytes from buffer and speak in vc
        if len(speech_response) > 0:
            sink.freshen(idx,username)
            try:
                audio_file = client.tts_worker(speech_response)

                # Play hotkey for controlling VTuber
                client.vts_worker.play_hotkey_using_message(speech_response)

                # Start speaking while hotkey is playing
                source = discord.FFmpegPCMAudio(audio_file)
                client.vc.play(source)
            except Exception as err:
                print(f"Error occured while playing TTS in response to text: {err}")

