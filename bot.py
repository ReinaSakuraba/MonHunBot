import os
import inspect
import traceback
from pathlib import Path

import discord
from discord.ext import commands

import config
import utils


class Bot(commands.Bot):
    def __init__(self, *, pool, **kwargs):
        super().__init__(command_prefix='mhw!', case_insensitive=True,
                          pm_help=None, game=discord.Game(name='mhw!help'))

        self.pool = pool

        startup_extensions =  [f'cogs.{x.stem}' for x in Path('cogs').glob('*.py')]
        for extension in startup_extensions:
            try:
                self.load_extension(extension)
            except Exception as e:
                print(f'Failed to load extension {extension}')
                traceback.print_exc()

        self.add_command(self.invite)
        self.add_command(self.source)

    async def on_ready(self):
        print(f'Logged in as {self.user}')
        print('---------')

    async def on_message(self, message):
        if message.author.bot:
            return

        await self.process_commands(message)

    @commands.command()
    async def invite(self, ctx):
        """Invite the bot to a server."""

        app_info = await self.application_info()

        permissions = discord.Permissions()
        permissions.read_messages = True
        permissions.send_messages = True
        permissions.embed_links = True

        invite = discord.utils.oauth_url(app_info.id, permissions=permissions)
        await ctx.send(invite)

    @commands.command(aliases=['github'])
    async def source(self, ctx, *, command: utils.CommandConverter = None):
        """Posts the source code for the bot."""

        source_url = await self.get_github_url()

        if command is None:
            return await ctx.send(source_url)

        src = getattr(command, 'callback', command.__class__)

        lines, first_line = inspect.getsourcelines(src)
        last_line = first_line + len(lines) - 1
        module = src.__module__
        if not module.startswith('discord'):
            location = os.path.relpath(inspect.getfile(src))
            branch, _ = await utils.run_subprocess('git rev-parse HEAD')
            branch = branch.strip()
        else:
            location = f'{module.replace(".", "/")}.py'
            source_url = 'https://github.com/Rapptz/discord.py'
            branch = 'rewrite'

        final_url = f'{source_url}/blob/{branch}/{location}#L{first_line}-L{last_line}'
        await ctx.send(final_url)

    async def get_github_url(self):
        result, _ = await utils.run_subprocess('git remote get-url origin')
        return result.strip()[:-4]
