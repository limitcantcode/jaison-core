from discord.ext import voice_recv
import discord
from .base import BaseCommandGroup
from .sink import BufferSink
from utils.logging import create_sys_logger
logger = create_sys_logger(id='discord')

# Grouping of slash commands into a command list
class VoiceCommandGroup(BaseCommandGroup):
    def __init__(self, params={}):
        super().__init__(params)

        self.command_list = [
            join_vc,
            leave_vc
        ]

async def _disconnect_client_if_connected(client: discord.Client) -> bool:
    '''Disconnect client from vc if in one and return whether client performed a dc or not'''
    if client.vc is not None and client.vc.is_connected():
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
    logger.info(f"Joining VC: {channel}...")
    audio_buffer = BufferSink(interaction.client.voice_cb)

    try:
        await _disconnect_client_if_connected(interaction.client) # client cannot connect if it is already in a vc
        interaction.client.vc = await channel.connect(cls=voice_recv.VoiceRecvClient)
        interaction.client.vc.listen(audio_buffer)
        await interaction.response.send_message(f"Joined {channel}.")
    except Exception as err:
        logger.error(f"Failed to join voice call: {err}")
        await interaction.response.send_message(f"Failed to join {channel}...")

@discord.app_commands.command(description="Leave current voice channel.", name="leave_vc")
async def leave_vc(interaction) -> None:
    '''Disconnect client from current vc'''
    logger.info("Leaving VC...")
    try:
        if not await _disconnect_client_if_connected(interaction.client):
            raise NotInVCException()
        await interaction.response.send_message(f"Left voice channel")
    except NotInVCException as err:
        logger.error(f"Not in voice call: {err}")
        await interaction.response.send_message(f"Not in a voice channel..")
        return
    except Exception as err:
        logger.error(f"Failed to leave voice call: {err}")
        await interaction.response.send_message(f"Failed to leave current voice channel...")
        return

