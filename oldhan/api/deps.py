from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from oldhan.engine.builder import build_dialogue_engine
from oldhan.engine.dialogue_engine import DialogueEngine
from oldhan.infrastructure import database
from oldhan.repository.dialogue_state_repository import DialogueStateRepository
from oldhan.service.dialogue_service import DialogueService




@lru_cache
def get_dialogue_service()->DialogueService:
    return DialogueService()

async def get_session()->AsyncSession:
    async with database.session_factory() as session:
        yield session

@lru_cache()
def get_dialogue_state_repository(
        session:AsyncSession = Depends(get_session)
)->DialogueStateRepository:
    return DialogueStateRepository(session)

@lru_cache()
def get_dialogue_engine()->DialogueEngine:
   return build_dialogue_engine()

#可以当作池来用,一个dialogue_service实例多次用
@lru_cache
def get_dialogue_service(
        repository: DialogueStateRepository = Depends(get_dialogue_state_repository),
        engine: DialogueEngine = Depends(get_dialogue_engine),
)->DialogueService:
    return DialogueService(repository,engine)