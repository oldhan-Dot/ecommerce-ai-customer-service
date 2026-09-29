from typing import Any, Dict

from oldhan.domain.state import DialogueState
from oldhan.task.action.base import Action, ActionResult


class ActionListen(Action):
    name = "action_listen"
    async def run(self,state:DialogueState,args:Dict[str,Any])->ActionResult:
        pass