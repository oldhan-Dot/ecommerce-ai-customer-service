from dataclasses import field, dataclass
from typing import Dict, Any

from oldhan.domain.state import DialogueState
from oldhan.task.action.registry import ActionRegistry


# 定义内循环返回外循环的ActionCall
@dataclass(slots=True)
class ActionCall:
    action_name: str
    action_args: Dict[str, Any] = field(default_factory=dict)


class ActionRunner:
    # 定义初始化方法，在创造ActionRunner实例的时候必须传入参数registry，使runner去调用对应的Action()
    def __init__(self, registry: ActionRegistry): #这里传入的registry是ActionRegistry的实例对象
        self.registry = registry  # 定义registry = 传入的registry

        async def execute_action(self, action_call: ActionCall, state: DialogueState):
            # 1.从action_call中获取action_name
            action_name = action_call.action_name
            # 2.根据action_name获取对应的Action类的对象(实例)
            action = self.registry.get(action_name)
            # 3.使用Action类实例调用run方法
            return await action.run(state, action_call.action_args)
