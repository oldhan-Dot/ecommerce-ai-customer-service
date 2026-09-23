import time
from dataclasses import dataclass, field
from typing import Any, Dict

from oldhan.domain.contexts import TaskContext, SystemContext
from oldhan.domain.messages import UserMessage, BotMessage


#DialogueState:用户的状态结构

#聚焦对象
@dataclass(slots=True)
class FocusedObject:
    type: str
    id: str
    title: str
    attributes: dict[str,Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls,raw_fo:Dict[str,Any])->"FocusedObject":
        return cls(**raw_fo)

#一轮对话
@dataclass(slots=True)
class Turn:
    """
        对话轮次：一个Turn实例表示一轮对话
        """
    turn_id: str
    input_message: UserMessage
    assistant_message: list[BotMessage] = field(default_factory=list)

    @classmethod
    def from_dict(cls,data:Dict[str,Any])->"Turn":
        return cls(
            turn_id=data["turn_id"],
            input_message = UserMessage.from_dict(data["input_message"]),
            assistant_message = [BotMessage.from_dict(m) for m in data.get("assistant_message",[])]
        )

#会话
@dataclass(slots=True)
class Session:
    """
        用户会话：当两条消息之间的时间间隔超过【1小时】时，会话结束
        """
    session_id: str
    started_at: float
    last_activity_at: float
    closed_at: float
    turns : list[Turn] = field(default_factory=list)

    @classmethod
    def from_dict(cls,data:Dict[str,Any])->"Session":
        return cls(
            session_id=data["session_id"],
            started_at=data.get("started_at",time.time()),
            last_activity_at=data.get("last_activity_at",time.time()),
            closed_at=data.get("closed_at"),
            turns = [Turn.from_dict(turn) for turn in data.get("turns",[])],
        )


#定义整个会话状态
@dataclass(slots=True)
class DialogueState:
    sender_id: str
    active_task:TaskContext | None = None
    paused_tasks:list[TaskContext] = field(default_factory=list)
    active_system_task:SystemContext | None = None
    focused_object: FocusedObject | None = None
    sessions:list[Session] = field(default_factory=list)
    current_session_id: str | None = None
    pending_turn : Turn | None = None

    @classmethod
    def from_dict(cls,data:Dict[str,Any])->"DialogueState":
        """从字典还原 DialogueState。"""
        state = cls(sender_id=data["sender_id"])
        #当前用户任务
        raw_task = data.get("active_task",None)
        state.active_task = TaskContext.from_dict(raw_task) if raw_task is not None else None
        #挂起任务
        state.paused_tasks = [TaskContext.from_dict(t) for t in data.get("paused_tasks",[])]
        #系统任务
        raw_sys = data.get("active_system_task",None)
        state.active_system_task = SystemContext.from_dict(raw_sys) if raw_sys is not None else None

        raw_fo = data.get("focused_object",None)
        state.focused_object = FocusedObject.from_dict(raw_fo) if raw_fo is not None else None
        state.sessions = [Session.from_dict(s) for s in data.get("sessions",[])]
        state.current_session_id = data.get("current_session_id",None)
        return state