from dataclasses import dataclass, field
from typing import Any

#commands:[{command:str,flow:flow_id}]可能含有多个command
#将llm生成的json命令传入Command中转换为对象格式
@dataclass(slots=True)
class Command:
    command: str
    @classmethod
    def from_dict(cls,command_dict:dict) -> 'Command':
        return COMMAND_CLASSES[command_dict.get("command")](**command_dict)

@dataclass(slots=True)
class StartFlowCommand(Command):
    flow : str

@dataclass(slots=True)
class SetSlotsCommand(Command):
    slots:dict[str, Any]=field(default_factory=dict)
@dataclass(slots=True)
class CancelFlowCommand(Command):
    pass
@dataclass(slots=True)
class ResumeFlowCommand(Command):
    flow : str

COMMAND_CLASSES = {
    "start_flow": StartFlowCommand,
    "set_slots": SetSlotsCommand,
    "cancel_flow": CancelFlowCommand,
    "resume_flow": ResumeFlowCommand,
}