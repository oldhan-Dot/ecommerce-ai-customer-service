from typing import List

from oldhan.knowledge.providers import KnowledgeProvider, KnowledgeChunk


class KnowledgeProviderRegistry:

    def __init__(self,providers:List[KnowledgeProvider]):
        self._providers = {p.provider_id:p for p in providers}

    def get(self,provider_id:str)->KnowledgeProvider:
        return self._providers[provider_id]