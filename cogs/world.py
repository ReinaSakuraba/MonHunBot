import re
import json
import shlex
import argparse

import discord
from discord.ext import commands

import utils


class Arguments(argparse.ArgumentParser):
    def error(self, message):
        raise RuntimeError(message)


class World:
    charm_re = re.compile(r"(?P<name>[\w' ]+?(?= Charm| [\dI]+)|[\w' ]+)( )?(?(2)(Charm))( )?(?(4)(?P<level>[\dI]+))", re.IGNORECASE)
    deco_re = re.compile(r"(?P<name>[\w' ]+?(?= Jewel| [\dI]+)|[\w' ]+)( )?(?(2)(Jewel))( )?(?(4)(?P<level>[\dI]+))", re.IGNORECASE)

    def __init__(self):
        with open('mhw/motionvalues.json') as f:
            self.motion_values = json.load(f)

    @commands.command()
    async def charm(self, ctx, *, name: str.lower):
        """Shows information about Charms."""

        match = self.charm_re.match(name)
        name = match.group('name')

        query = """
                SELECT
                    charms.name,
                    STRING_AGG(DISTINCT skill || ' ' || level, ', ') AS skills,
                    STRING_AGG(DISTINCT material || ' x' || amount, ', ') AS materials
                FROM world.charms
                JOIN world.charm_skills
                ON charms.name = charm_skills.name
                LEFT JOIN world.charm_materials
                ON charms.name = charm_materials.name
                WHERE charms.name ILIKE $1 || ' Charm%'
                GROUP BY charms.name
                ORDER BY charms.name;
                """
        records = await ctx.bot.pool.fetch(query, name)

        if not records:
            return await self.show_possibilities(ctx, 'charms', name)

        embed = discord.Embed(title=f'{name.title()} Charm')

        skills = [f'{"I" * index} - {skills}' for index, (_, skills, _) in enumerate(records, 1)]
        embed.add_field(name='Skills', value='\n'.join(skills))

        if records[0]['materials'] is not None:
            mats = [f'{"I" * index} - {materials}' for index, (*_, materials) in enumerate(records, 1)]
            embed.add_field(name='Materials', value='\n'.join(mats), inline=False)

        await ctx.send(embed=embed)

    @commands.command()
    async def mv(self, ctx, *, weapon: str.lower):
        """Shows the motion values for weapons."""

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
        """Shows information about skills."""

        query = """
                SELECT
                    skills.name,
                    description,
                    STRING_AGG(DISTINCT 'Lv ' || skill_levels.level || ' - ' || effect, E'\n') AS levels,
                    STRING_AGG(DISTINCT  armor_skills.name || ' - ' || armor_skills.level || ' points', E'\n') AS armors,
                    STRING_AGG(DISTINCT  charm_skills.name || ' - ' || charm_skills.level || ' points', E'\n') AS charms,
                    decorations.name AS decoration
                FROM world.skills
                LEFT JOIN world.skill_levels
                ON skills.name = skill_levels.name
                LEFT JOIN world.armor_skills
                ON skills.name = armor_skills.skill
                LEFT JOIN world.charm_skills
                ON skills.name = charm_skills.skill
                LEFT JOIN world.decorations
                ON skills.name = decorations.skill
                WHERE LOWER(skills.name)=$1
                GROUP BY skills.name, decoration;
                """
        record = await ctx.bot.pool.fetchrow(query, name)

        if record is None:
            return await self.show_possibilities(ctx, 'skills', name)

        name, description, levels, armors, charms, decoration = record

        embed = discord.Embed(title=name)
        embed.description = description

        if levels:
            embed.add_field(name='Levels', value=levels)

        if armors:
            embed.add_field(name='Armor', value=armors, inline=False)

        if charms:
            embed.add_field(name='Charm', value=charms, inline=False)

        if decoration:
            embed.add_field(name='Decoration', value=decoration)

        await ctx.send(embed=embed)

    @commands.command(aliases=['deco'])
    async def decoration(self, ctx, *, name: str.lower):
        """Shows information about decorations."""

        match = self.deco_re.match(name)

        name = match.group('name')

        query = """
                SELECT name, skill, rarity
                FROM world.decorations
                WHERE name ILIKE $1 || ' Jewel%';
                """
        record = await ctx.bot.pool.fetchrow(query, name)

        if record is None:
            return await self.show_possibilities(ctx, 'decorations', name)

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

    @commands.group(invoke_without_command=True, case_insensitive=True)
    async def armor(self, ctx, *, name: str.lower):
        """Shows information for armor."""

        query = """
                SELECT
                    armors.name,
                    rarity,
                    price,
                    part,
                    min_def || '~' || max_def AS def,
                    slot_levels,
                    fire_res,
                    water_res,
                    thunder_res,
                    ice_res,
                    dragon_res,
                    STRING_AGG(DISTINCT material || ' x' || amount, ', ') AS materials,
                    STRING_AGG(DISTINCT skill || ' ' || level, ', ') AS skills
                FROM world.armors
                LEFT JOIN world.armor_materials
                ON armors.name = armor_materials.name
                LEFT JOIN world.armor_skills
                ON armors.name = armor_skills.name
                WHERE LOWER(armors.name) = $1
                GROUP BY armors.name;
                """

        record = await ctx.bot.pool.fetchrow(query, name)
        if record is None:
            return await self.show_possibilities(ctx, 'armors', name)

        name, rarity, price, part, defense, slots, fire_res, water_res, thunder_res, ice_res, dragon_res, mats, skills = record

        e_def = '<:mhw_def:429038203832369172>'
        e_fire = '<:mhw_fire:429038203475853314>'
        e_water = '<:mhw_water:429038204042215424>'
        e_thunder = '<:mhw_thunder:429038203622653973>'
        e_ice = '<:mhw_ice:429038203832369152>'
        e_dragon = '<:mhw_dragon:429038203719122945>'
        e_wide1 = '<:mhw_1wide:429038203920449536>'
        e_wide2 = '<:mhw_2wide:429038203551481857>'
        e_wide3 = '<:mhw_3wide:429038203698282497>'

        slot_transform = {
            1: e_wide1,
            2: e_wide2,
            3: e_wide3
        }

        slots = ' '.join(filter(None, map(slot_transform.get, slots))) or 'None'
        defenses = f'{e_def}: {defense}\n{e_fire}: {fire_res}\n{e_water}: {water_res}\n{e_thunder}: {thunder_res}' \
                   f'\n{e_ice}: {ice_res}\n{e_dragon}: {dragon_res}'

        embed = discord.Embed(title=name)
        embed.add_field(name='Rarity', value=rarity)
        embed.add_field(name='Price', value=price)
        embed.add_field(name='Part', value=part)
        embed.add_field(name='Defenses', value=defenses, inline=False)
        embed.add_field(name='Slots', value=slots)
        if mats:
            embed.add_field(name='Materials', value=mats, inline=False)
        if skills:
            embed.add_field(name='Skills', value=skills, inline=False)

        await ctx.send(embed=embed)

    @armor.command(name='search')
    async def armor_search(self, ctx, *, args: str):
        """Searches for armor.

        Search options are chosen by doing --option value
        The following options are valid.
        slots: The slots the armor should have,
        part: The type of armor to search for.
        """

        parser = Arguments(add_help=False, allow_abbrev=False)
        parser.add_argument('--slots', type=int, nargs='+', choices=(0, 1, 2, 3))
        parser.add_argument('--part', type=str, choices=('Head', 'Torso', 'Arms', 'Waist', 'Legs'))

        try:
            args = parser.parse_args(shlex.split(args))
        except Exception as e:
            return await ctx.send(e)

        pred = ''

        if args.slots:
            if len(args.slots) > 3:
                return await ctx.send('Slot amount may not be greater than 4.')

            args.slots.extend([0, 0])
            pred += f"""
                    AND slot_levels[1] >= {args.slots[0]}
                    AND slot_levels[2] >= {args.slots[1]}
                    AND slot_levels[3] >= {args.slots[2]}
                    """

        if args.part:
            pred += f"""
                    AND part = '{args.part}'
                    """

        query = f"""
                SELECT
                    STRING_AGG(name, E'\n')
                FROM world.armors
                WHERE 1=1
                {pred}
                """
        names = await ctx.bot.pool.fetchval(query)

        await ctx.send(names or 'No armor found.')

    async def show_possibilities(self, ctx, table_name, name):
        query = f"""
                SELECT
                    STRING_AGG(name, E'\n' ORDER BY SIMILARITY(name, $1) DESC)
                FROM world.{table_name}
                WHERE name % $1;
                """
        possibilities = await ctx.bot.pool.fetchval(query, name)
        if possibilities is None:
            return await ctx.send(f'{table_name.title()[:-1]} not found.')

        return await ctx.send(f'{table_name.title()[:-1]} not found. Did you mean...\n{possibilities}')


def setup(bot):
    bot.add_cog(World())
