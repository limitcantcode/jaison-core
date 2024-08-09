'''
Augment given Discord bot with cogs (additional functionality) in cogs_list

NOTE: cog files are required to have a `setup(bot)` function to be able to add the cog
'''

def setup_cogs(bot):

    # strings in cogs_list are file_names in this directory
    cogs_list = [
        'voice'
    ]

    for cog in cogs_list:
        bot.load_extension(f'cogs.{cog}')