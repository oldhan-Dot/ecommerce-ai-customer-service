from typing import Dict

from oldhan.task.action.base import Action


#定义ActionRegistry:runner可以通过action_registry使用action_name调用Action类方法

class ActionRegistry:
    def __init__(self):
        self._actions : Dict[str, Action]={}

    def register(self, action : Action): #把 Action 按照它的 name 存进 _actions 字典
        self._actions[action.name] = action

    def get(self,action_name:str)->Action:
        if action_name not in self._actions:
            raise KeyError(f"Action {action_name} not registered")
        return self._actions[action_name]