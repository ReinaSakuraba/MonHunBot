import json
import asyncio

import asyncpg

import config
from bot import Bot


async def create_db(pool):
    query = f"""
            CREATE SCHEMA IF NOT EXISTS world;

            CREATE TABLE IF NOT EXISTS world.armor_skills (
                name TEXT,
                skill TEXT REFERENCES world.skills(name),
                level SMALLINT NOT NULL,
                PRIMARY KEY(name, skill)
            );

            CREATE TABLE IF NOT EXISTS world.skills (
                name TEXT PRIMARY KEY,
                description TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS world.skill_levels (
                name TEXT REFERENCES world.skills(name),
                level SMALLINT,
                effect TEXT NOT NULL,
                PRIMARY KEY(name, level)
            );

            CREATE TABLE IF NOT EXISTS world.charms (
                name TEXT PRIMARY KEY
            );

            CREATE TABLE IF NOT EXISTS world.charm_skills (
                name TEXT REFERENCES world.charms(name),
                skill TEXT REFERENCES world.skills(name),
                level SMALLINT NOT NULL,
                PRIMARY KEY(name, skill)
            );

            CREATE TABLE IF NOT EXISTS world.charm_materials (
                name TEXT REFERENCES world.charms(name),
                material TEXT,
                amount SMALLINT NOT NULL,
                PRIMARY KEY(name, material)
            );

            CREATE TABLE IF NOT EXISTS world.decorations (
                name TEXT PRIMARY KEY,
                slot_level SMALLINT NOT NULL,
                rarity SMALLINT NOT NULL,
                skill TEXT REFERENCES world.skills(name) NOT NULL
            );
            """

    await pool.execute(query)

    query = """
            INSERT INTO world.armor_skills (
                name,
                skill,
                level
            ) VALUES ($1, $2, $3)
            ON CONFLICT (name, skill)
            DO UPDATE
            SET level = excluded.level;
            """

    with open('mhw/armor.json') as f:
        armors = json.load(f)

    for armor in armors:
        for skill in armor['Skills']:
            await pool.execute(query, armor['Name'], skill['Name'], skill['Level'])

    query = """
            INSERT INTO world.skills (
                name,
                description
            ) VALUES ($1, $2)
            ON CONFLICT (name)
            DO UPDATE
            SET description = excluded.description;
            """

    with open('mhw/skills.json') as f:
        skills = json.load(f)

    for skill in skills:
        await pool.execute(query, skill["Name"], skill["Description"])

    query = """
            INSERT INTO world.skill_levels (
                name,
                level,
                effect
            ) VALUES ($1, $2, $3)
            ON CONFLICT (name, level)
            DO UPDATE
            SET effect = excluded.effect
            """

    for skill in skills:
        levels = skill.get('Levels')
        if levels is None:
            continue

        for level, effect in enumerate(levels, 1):
            await pool.execute(query, skill['Name'], level, effect)

    with open('mhw/charms.json') as f:
        charms = json.load(f)

    query = """
            INSERT INTO world.charms (
                name
            ) VALUES ($1)
            ON CONFLICT (name)
            DO NOTHING;
            """

    for charm in charms:
        await pool.execute(query, charm['Name'])

    query = """
            INSERT INTO world.charm_skills (
                name,
                skill,
                level
            ) VALUES ($1, $2, $3)
            ON CONFLICT (name, skill)
            DO UPDATE
            SET level = excluded.level;
            """

    for charm in charms:
        for skill in charm['Skills']:
            await pool.execute(query, charm['Name'], skill['Name'], skill['Level'])

    query = """
            INSERT INTO world.charm_materials (
                name,
                material,
                amount
            ) VALUES ($1, $2, $3)
            ON CONFLICT (name, material)
            DO UPDATE
            SET amount = excluded.amount;
            """

    for charm in charms:
        materials = charm.get('Materials')
        if materials is None:
            continue

        for material in materials:
            await pool.execute(query, charm['Name'], material['Name'], material['Amount'])

    query = """
            INSERT INTO world.decorations (
                name,
                slot_level,
                rarity,
                skill
            ) VALUES ($1, $2, $3, $4)
            ON CONFLICT (name)
            DO UPDATE
            SET
                slot_level = excluded.slot_level,
                rarity = excluded.rarity,
                skill = excluded.skill;
            """

    with open('mhw/decorations.json') as f:
        decorations = json.load(f)

    for decoration in decorations:
        await pool.execute(query, decoration['Name'], decoration['Slot Level'], decoration['Rarity'], decoration['Skill'])


def main():
    loop = asyncio.get_event_loop()
    pool = loop.run_until_complete(asyncpg.create_pool(config.dsn, command_timeout=60))
    loop.run_until_complete(create_db(pool))
    bot = Bot(pool=pool, loop=loop)
    bot.run(config.token)


if __name__ == '__main__':
    main()
