import re
import json

import discord
from discord.ext import commands

import utils


class World:
    charm_re = re.compile(r"(?P<name>[\w' ]+?(?= Charm| [\dI]+)|[\w' ]+)( )?(?(2)(Charm))( )?(?(4)(?P<level>[\dI]+))", re.IGNORECASE)
    deco_re = re.compile(r"(?P<name>[\w' ]+?(?= Jewel| [\dI]+)|[\w' ]+)( )?(?(2)(Jewel))( )?(?(4)(?P<level>[\dI]+))", re.IGNORECASE)

    def __init__(self):
        with open('mhw/motionvalues.json') as f:
            self.motion_values = json.load(f)

    @commands.command()
    async def charm(self, ctx, *, name: str.lower):
        match = self.charm_re.match(name)
        name = match.group('name')

        query = """
                SELECT
                    charms.name,
                    STRING_AGG(skill || ' ' || level, ', ') AS skills
                FROM world.charms
                JOIN world.charm_skills
                ON charms.name = charm_skills.name
                WHERE charms.name ILIKE $1 || ' Charm%'
                GROUP BY charms.name
                ORDER BY charms.name;
                """
        records = await ctx.bot.pool.fetch(query, name)

        if records is None:
            return await ctx.send('Charm not found')

        embed = discord.Embed(title=f'{name.title()} Charm')

        skills = [f'{"I" * index} - {skills}' for index, (_, skills) in enumerate(records, 1)]
        embed.add_field(name='Skills', value='\n'.join(skills))

        query = """
                SELECT
                    charms.name,
                    STRING_AGG(material || ' x' || amount, ', ') AS materials
                FROM world.charms
                LEFT JOIN world.charm_materials
                ON charms.name = charm_materials.name
                WHERE charms.name ILIKE $1 || ' Charm%'
                GROUP BY charms.name
                ORDER BY charms.name;
                """
        records = await ctx.bot.pool.fetch(query, name)

        if records[0]['materials'] is not None:
            mats = [f'{"I" * index} - {materials}' for index, (_, materials) in enumerate(records, 1)]
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
            's&s': 'sword and shield',
            'sword and shield': 'sword and shield',
            'sword & shield': 'sword and shield',
            'sword&shield': 'sword and shield',
            'sword n shield': 'sword and shield',
            'sword \'n\' shield': 'sword and shield',
            'dbs': 'dual blades',
            'db': 'dual blades',
            'dual blades': 'dual blades',
            'dualblades': 'dual blades',
            'dual blade': 'dual blades',
            'dualblade': 'dual blades',
            'duals': 'dual blades',
            'hammer': 'hammer',
            'hh': 'hunting horn',
            'horn': 'hunting horn',
            'hunting horn': 'hunting horn',
            'huntinghorn': 'hunting horn',
            'lance': 'lance',
            'gl': 'gunlance',
            'gunlance': 'gunlance',
            'gun lance': 'gunlance',
            'sa': 'switch axe',
            'axe': 'switch axe',
            'switch axe': 'switch axe',
            'switchaxe': 'switch axe',
            'cb': 'charge blade',
            'charge blade': 'charge blade',
            'chargeblade': 'charge blade',
            'ig': 'insect glaive',
            'glaive': 'insect glaive',
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
            'bullets': 'shot',
            'ammo': 'shot',
            'ammos': 'shot'
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

    @commands.command()
    async def skill(self, ctx, *, name: str.lower):
        query = """
                SELECT skills.name, description, level, effect
                FROM world.skills
                LEFT JOIN world.skill_levels
                ON skills.name = skill_levels.name
                WHERE LOWER(skills.name)=$1
                ORDER BY level;
                """
        records = await ctx.bot.pool.fetch(query, name)

        if not records:
            query = """
                    SELECT ARRAY(
                        SELECT name
                        FROM world.skills
                        WHERE name % $1
                        ORDER BY SIMILARITY(name, $1) DESC
                    );
                    """
            possible_skills = await ctx.bot.pool.fetchval(query, name)
            if not possible_skills:
                return await ctx.send('Skill not found.')

            names = '\n'.join(possible_skills)
            return await ctx.send(f'Skill not found. Did you mean...\n{names}')

        name, description, *_ = records[0]

        embed = discord.Embed(title=name)
        embed.description = description

        levels = [(r['level'], r['effect']) for r in records]
        if levels[0][0] is not None:
            embed.add_field(name='Levels', value='\n'.join(f'Lv {level} - {effect}' for level, effect in levels))

        query = """
                SELECT name, level
                FROM world.charm_skills
                WHERE skill=$1
                ORDER BY level;
                """
        charms = await ctx.bot.pool.fetch(query, name)

        if charms:
            fmt = '\n'.join(f'{name} - {level} points' for name, level in charms)
            embed.add_field(name='Charm', value=fmt, inline=False)

        query = """
                SELECT name
                FROM world.decorations
                WHERE skill=$1;
                """
        jewel = await ctx.bot.pool.fetchval(query, name)

        if jewel:
            embed.add_field(name='Jewel', value=jewel)

        await ctx.send(embed=embed)

    @commands.command()
    async def decoration(self, ctx, *, name: str.lower):
        match = self.deco_re.match(name)

        name = match.group('name')

        query = """
                SELECT name, skill, rarity
                FROM world.decorations
                WHERE name ILIKE $1 || ' Jewel%';
                """
        record = await ctx.bot.pool.fetchrow(query, name)

        if record is None:
            query = """
                    SELECT ARRAY(
                        SELECT name
                        FROM world.decorations
                        WHERE name % $1
                        ORDER BY SIMILARITY(name, $1) DESC
                    );
                    """
            possible_decos = await ctx.bot.pool.fetchval(query, name)
            if not possible_decos:
                return await ctx.send('Decoration not found.')

            names = '\n'.join(possible_decos)
            return await ctx.send(f'Decoration not found. Did you mean...\n{names}')

        name, skill, rarity = record

        embed = discord.Embed(title=name)
        embed.add_field(name='Skill', value=skill)
        embed.add_field(name='Rarity', value=rarity)

        drop_rates = {
            5: 'Mysterious: 3.036%\nGlowing: 2.321%\nWorn: 0.357%\nWarped: 0%',
            6: 'Mysterious: 0.429%\nGlowing: 0.971%\nWorn: 2.3437%\nWarped: 2.2%',
            7: 'Mysterious: 0%\nGlowing: 0.045%\nWorn: 0.273%\nWarped: 0.818%',
            8: 'Mysterious: 0%\nGlowing: 0%\nWorn: 0.167%\nWarped: 0.417%'
        }

        embed.add_field(name='Drop Rates', value=drop_rates[rarity], inline=False)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(World())
