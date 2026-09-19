import asyncio

from sqlalchemy import text

from oldhan.infrastructure import database



async def test_db():
    database.init_db_engine_and_session_factory()
    async with database.session_factory() as session:
        result = await session.execute(text("select 1"))
        print(result.all())
    await database.close_db_engine()

if __name__ == '__main__':
    asyncio.run(test_db())