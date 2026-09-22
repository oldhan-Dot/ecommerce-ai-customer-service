from functools import lru_cache

from oldhan.service.dialogue_service import DialogueService



#可以当作池来用,一个dialogue_service实例多次用
@lru_cache
def get_dialogue_service()->DialogueService:
    return DialogueService()