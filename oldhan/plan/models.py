from dataclasses import dataclass, field

from oldhan.clarify.reasons import ClarifyReason
from oldhan.task.commands.models import Command
#TurnPlan是决定进入哪个任务处理流程，command是taskhandle处理链路中的几个任务步骤命令

@dataclass(slots=True)
class TaskTurnPlan:
    commands:list[Command] = field(default_factory=list)
    @classmethod
    def from_dict(cls,dict_data:dict)->"TaskTurnPlan":
        #必须用列表推导(方括号)并写 commands=:
        #  写成 cls(生成器) 会让 commands 变成 generator 对象,只能遍历一次,且 len() 会报错
        return cls(
            commands=[Command.from_dict(command_dict) for command_dict in dict_data.get("commands",[])]
        )

@dataclass(slots=True)
class KnowledgeTurnPlan:
    intents : list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls,dict_data:dict)->"KnowledgeTurnPlan":
        return cls(
            intents = dict_data.get("intents",[]),
        )

@dataclass(slots=True)
class ChitChatTurnPlan:
    pass


@dataclass(slots=True)
class TurnPlan:
    task : TaskTurnPlan | None = None
    knowledge : KnowledgeTurnPlan | None = None
    chitchat : ChitChatTurnPlan | None = None

    @classmethod
    def from_dict(cls,dict_data:dict)->"TurnPlan":
        return cls(
            task = TaskTurnPlan.from_dict(dict_data.get("task")) if dict_data.get("task") is not None else None,
            #注意:这里不能写 xxx is not None —— 那会让 knowledge 变成 True/False 而不是对象
            knowledge = KnowledgeTurnPlan.from_dict(dict_data.get("knowledge")) if dict_data.get("knowledge") else None,
            chitchat = ChitChatTurnPlan() if dict_data.get("chitchat") is not None else None
        )
@dataclass(slots=True)
class TurnPlanValidationResult:
    valid: bool
    reason: ClarifyReason | None = None
