import discord
from .voice import VoiceCommandGroup

'''
Create a command tree for the given client. This adds slash commands
to your bot and will be registered after syncing.
Learn more about command tree's here: https://discordpy.readthedocs.io/en/stable/interactions/api.html#discord.app_commands.CommandTree

Returns a CommandTree, {tree params}
'''
def add_commands(client: discord.Client, server_id: str):

    params = {}
    if server_id is not None:
        params['guild'] = discord.Object(server_id)

    # Initialize tree for client
    tree = discord.app_commands.CommandTree(client)
    tree.clear_commands(**params)

    # List of command group setups
    VoiceCommandGroup(params=params).setup(tree)

    # Returning final tree
    return tree, params