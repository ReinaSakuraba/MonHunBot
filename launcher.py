import json
import asyncio

import asyncpg

import config
from bot import Bot


async def create_db(pool):
    query = f"""
            CREATE SCHEMA IF NOT EXISTS world;

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

            CREATE TABLE IF NOT EXISTS world.charm_skills (
                name TEXT,
                skill TEXT,
                level SMALLINT NOT NULL,
                PRIMARY KEY(name, skill)
            );
            """

    await pool.execute(query)

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

    with open('mhw/charms.json') as f:
        charms = json.load(f)

    for charm in charms.values():
        for level in charm['Levels']:
            for skill in level['Skills']:
                await pool.execute(query, level['Name'], skill['Name'], skill['Level'])


def main():
    loop = asyncio.get_event_loop()
    pool = loop.run_until_complete(asyncpg.create_pool(config.dsn, command_timeout=60))
    loop.run_until_complete(create_db(pool))
    bot = Bot(pool=pool, loop=loop)
    bot.run(config.token)


if __name__ == '__main__':
    main()
