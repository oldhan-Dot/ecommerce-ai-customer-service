from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from oldhan.engine.builder import build_dialogue_engine
from oldhan.engine.dialogue_engine import DialogueEngine
from oldhan.infrastructure import database
from oldhan.repository.dialogue_state_repository import DialogueStateRepository
from oldhan.service.dialogue_service import DialogueService
from oldhan.service.history_service import HistoryService


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

@lru_cache
def get_dialogue_service(
        repository: DialogueStateRepository = Depends(get_dialogue_state_repository),
        engine: DialogueEngine = Depends(get_dialogue_engine),
)->DialogueService:
    return DialogueService(repository,engine)

@lru_cache()
def get_history_service(
        repository: DialogueStateRepository = Depends(get_dialogue_state_repository),
):
    return HistoryService(repository)