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
                description TEXT NOT NULL,
                levels TEXT[]
            );
            """

    await pool.execute(query)

    query = """
            INSERT INTO world.skills (
                name,
                description,
                levels
            ) VALUES ($1, $2, $3)
            ON CONFLICT (name)
            DO UPDATE
            SET
                name = excluded.name,
                description = excluded.description,
                levels = excluded.levels;
            """

    with open('mhw/skills.json') as f:
        skills = json.load(f)

    for skill in skills:
        await pool.execute(query, skill["Name"], skill["Description"], skill.get("Levels"))


def main():
    loop = asyncio.get_event_loop()
    pool = loop.run_until_complete(asyncpg.create_pool(config.dsn, command_timeout=60))
    loop.run_until_complete(create_db(pool))
    bot = Bot(pool=pool, loop=loop)
    bot.run(config.token)


if __name__ == '__main__':
    main()
