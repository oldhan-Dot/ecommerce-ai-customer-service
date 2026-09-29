from abc import ABC, abstractclassmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List

from oldhan.domain.messages import BotMessage
from oldhan.domain.state import DialogueState



@dataclass(slots=True)
class ActionResult:
    messages:List[BotMessage] = field(default_factory=list)
    slots_updates : Dict[str,Any] = field(default_factory=dict)

class Action(ABC):
    name : str

    @abstractclassmethod #抽象方法,子类必须重写方法
    async def run(self,state:DialogueState,args:Dict[str,Any])->ActionResult:
        pass

