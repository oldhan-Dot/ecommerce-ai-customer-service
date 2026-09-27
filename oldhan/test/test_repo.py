import asyncio

from oldhan.domain.state import DialogueState
from oldhan.infrastructure import database
from oldhan.repository.dialogue_state_repository import DialogueStateRepository
def test_load():
    database.init_db_engine_and_session_factory()

    async def test():
        async with database.session_factory() as session:
            repo = DialogueStateRepository(session)
            state: DialogueState = await repo.load("u1003")
            print("查询结果:", state)

        await database.close_db_engine()

    asyncio.run(test())


if __name__ == "__main__":
    test_load()