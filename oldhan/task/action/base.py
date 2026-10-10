from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List

from oldhan.domain.messages import BotMessage
from oldhan.domain.state import DialogueState



@dataclass(slots=True)
class ActionResult:
    messages:List[BotMessage] = field(default_factory=list)
    slot_updates : Dict[str,Any] = field(default_factory=dict)

class Action(ABC):
    name : str

    @abstractmethod #抽象方法,子类必须重写方法
    async def run(self,state:DialogueState,args:Dict[str,Any])->ActionResult:
        pass

