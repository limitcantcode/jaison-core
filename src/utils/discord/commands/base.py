import discord

'''
Abstract class for grouping slash commands to be registered into
a command tree. Command list should be instantiated in concrete class
with a list of valid app commands. 
'''
class BaseCommandGroup():
    def __init__(self, params={}):
        self.command_list = []
        self.params = params

    def setup(self, tree: discord.app_commands.CommandTree):
        for command in self.command_list:
            tree.add_command(command, **self.params)