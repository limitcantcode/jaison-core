import discord
from .voice import VoiceCommandGroup
from config import config

# Configure commands to be guild/server specific. Registered commands will only appear for that server.
# Ideal for development, otherwise commands will take up to an hour to register 
default_params = {}
if 'server_id' in config and config['server_id'] is not None:
    default_params['guild'] = discord.Object(id=config['server_id'])

'''
Create a command tree for the given client. This adds slash commands
to your bot and will be registered after syncing.
Learn more about command tree's here: https://discordpy.readthedocs.io/en/stable/interactions/api.html#discord.app_commands.CommandTree

Returns a CommandTree
'''
def add_commands(client: discord.Client):

    # Initialize tree for client
    tree = discord.app_commands.CommandTree(client)
    tree.clear_commands(**default_params)

    # List of command group setups
    VoiceCommandGroup(params=default_params).setup(tree)

    # Returning final tree
    return tree