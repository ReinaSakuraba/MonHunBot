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

        with open('mhw/motionvalues.json') as f:
            self.motion_values = json.load(f)

    @commands.command()
    async def charm(self, ctx, *, name: str.lower):
        match = self.charm_re.match(name)

        name = match.group('name')
        charm = self.charms.get(name)

        if charm is None:
            return await ctx.send(f'Charm {name} not found')

        embed = discord.Embed(title=f'{name.title()} Charm')

        skills = []
        for index, level in enumerate(charm["Levels"], 1):
            skill_levels = ", ".join(f'{skill["Name"]} {skill["Level"]}' for skill in level["Skills"])
            skills.append(f'{"I"* index} - {skill_levels}')

        embed.add_field(name='Skills', value='\n'.join(skills))

        try:
            mats = []
            for index, level in enumerate(charm["Levels"], 1):
                materials = ", ".join(f'{mat["Name"]} x{mat["Amount"]}' for mat in level["Materials"])
                mats.append(f'{"I"* index} - {materials}')
        except KeyError:
            pass
        else:
            embed.add_field(name='Materials', value='\n'.join(mats), inline=False)

        await ctx.send(embed=embed)

    @commands.command()
    async def mv(self, ctx, *, weapon: str.lower):
        transformations = {
            'gs': 'great sword',
            'great sword': 'great sword',
            'greatsword': 'great sword',
            'ls': 'long sword',
            'long sword': 'long sword',
            'longsword': 'long sword',
            'sns': 'sword and shield',
            'sword and shield': 'sword and shield',
            'sword n shield': 'sword and shield',
            'sword \'n\' shield': 'sword and shield',
            'dbs': 'dual blades',
            'dual blades': 'dual blades',
            'dualblades': 'dual blades',
            'dual blade': 'dual blades',
            'dual blades': 'dual blades',
            'duals': 'dual blades',
            'hammer': 'hammer',
            'hh': 'hunting horn',
            'hunting horn': 'hunting horn',
            'huntinghorn': 'hunting horn',
            'lance': 'lance',
            'gl': 'gunlance',
            'gunlance': 'gunlance',
            'gun lance': 'gunlance',
            'sa': 'switch axe',
            'switch axe': 'switch axe',
            'switchaxe': 'switch axe',
            'cb': 'charge blade',
            'charge blade': 'charge blade',
            'chargeblade': 'charge blade',
            'ig': 'insect glaive',
            'insect glaive': 'insect glaive',
            'insectglaive': 'insect glaive',
            'lbg': 'light bowgun',
            'light bowgun': 'light bowgun',
            'light bow gun': 'light bowgun',
            'lightbow gun': 'light bowgun',
            'lighbowgun': 'light bowgun',
            'hbg': 'heavy bowgun',
            'heavy bowgun': 'heavy bowgun',
            'heavy bow gun': 'heavy bowgun',
            'heavybow gun': 'heavy bowgun',
            'heavybowgun': 'heavy bowgun',
            'bow': 'bow',
            'shot': 'shot',
            'shots': 'shot',
            'bullet': 'shot',
            'bullets': 'shot'
        }

        weapon = transformations.get(weapon)
        if weapon is None:
            return await ctx.send('Weapon not found.')

        weapon_values = self.motion_values[weapon]

        table = utils.TabularData()
        table.set_columns(['Move', 'Damage Type', 'Motion Value/Stun/Exhaust'])
        for move, data in weapon_values.items():
            table.add_row([move, data['Damage Type'], f"{data['Motion Value']}/{data['Stun']}/{data['Exhaust']}"])

        render = table.render()
        paginator = commands.Paginator()
        for line in render.split('\n'):
            paginator.add_line(line)

        for p in paginator.pages:
            await ctx.send(p)


def setup(bot):
    bot.add_cog(World())
