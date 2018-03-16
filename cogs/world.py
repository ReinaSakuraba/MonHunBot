import re
import json

import discord
from discord.ext import commands

import utils


class World:
    charm_re = re.compile(r"(?P<name>[\w' ]+?(?= Charm| [\dI]+)|[\w' ]+)( )?(?(2)(Charm))( )?(?(4)(?P<level>[\dI]+))", re.IGNORECASE)

    def __init__(self):
        with open('mhw/charms.json') as f:
            self.charms = json.load(f)

    @commands.command()
    async def charm(self, ctx, *, name: str.lower):
        match = self.charm_re.match(name)
        if not match:
            return await ctx.send('ass')

        name = match.group('name')
        charm = self.charms.get(name)

        if charm is None:
            return await ctx.send(f'Charm {name} not found')

        embed = discord.Embed(title=f'{name.title()} Charm')

        skills = '\n'.join(f'{"I" * i} - {", ".join(level["Skills"])}' for i, level in enumerate(charm["Levels"], 1))
        embed.add_field(name='Skills', value=skills)

        try:
            mats = '\n'.join(f'{"I" * i} - {", ".join(level["Materials"])}' for i, level in enumerate(charm["Levels"], 1))
        except KeyError:
            pass
        else:
            embed.add_field(name='Materials', value=mats, inline=False)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(World())
