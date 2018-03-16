import traceback
from pathlib import Path

import discord
from discord.ext import commands

import config


class Bot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(command_prefix='mhw!', case_insensitive=True,
                          pm_help=None, game=discord.Game(name='mhw!help'))

        startup_extensions =  [f'cogs.{x.stem}' for x in Path('cogs').glob('*.py')]
        for extension in startup_extensions:
            try:
                self.load_extension(extension)
            except Exception as e:
                print(f'Failed to load extension {extension}')
                traceback.print_exc()

    async def on_ready(self):
        print(f'Logged in as {self.user}')
        print('---------')

    async def on_message(self, message):
        if message.author.bot:
            return

        await self.process_commands(message)


def main():
    bot = Bot()
    bot.run(config.token)


if __name__ == '__main__':
    main()
