import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List

from oldhan.domain.contexts import TaskContext, SystemContext
from oldhan.domain.messages import UserMessage, BotMessage, MessageObject


#DialogueState:用户的状态结构

#聚焦对象
@dataclass(slots=True)
class FocusedObject:
    type: str
    id: str
    title: str
    attributes: dict[str,Any] = field(default_factory=dict)

    def to_dict(self)->dict:
        return asdict(self)

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
    assistant_messages: list[BotMessage] = field(default_factory=list)

    def to_dict(self)->dict:
        return {
            "turn_id": self.turn_id,
            "input_message": self.input_message.to_dict(),
            "assistant_messages": [bot.to_dict() for bot in self.assistant_messages],
        }

    @classmethod
    def from_dict(cls,data:Dict[str,Any])->"Turn":
        return cls(
            turn_id=data["turn_id"],
            input_message = UserMessage.from_dict(data["input_message"]),
            assistant_messages = [BotMessage.from_dict(m) for m in data.get("assistant_messages",[])]
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
    closed_at: float | None = None
    turns : list[Turn] = field(default_factory=list)

    def to_dict(self)->dict:
        return {
            "session_id": self.session_id,
            "started_at": self.started_at,
            "last_activity_at": self.last_activity_at,
            "closed_at": self.closed_at,
            "turns": [turn.to_dict() for turn in self.turns],
        }

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


    def to_dict(self)->dict:
        return {
            "sender_id": self.sender_id,
            "active_task": self.active_task.to_dict() if self.active_task is not None else None,
            "paused_tasks": [task.to_dict() for task in self.paused_tasks],
            "active_system_task":self.active_system_task.to_dict() if self.active_system_task is not None else None,
            "focused_object" : self.focused_object.to_dict() if self.focused_object is not None else None,
            "sessions" : [session.to_dict() for session in self.sessions],
            "current_session_id": self.current_session_id,
            "pending_turn": self.pending_turn.to_dict() if self.pending_turn is not None else None,
        }

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

    def get_current_session(self) -> Session | None:
        if self.current_session_id is None:
            return None
        for session in self.sessions:
            if session.session_id == self.current_session_id:
                return session

    def start_session(self):
        now_time = time.time()
        new_session = Session(
            session_id=str(uuid.uuid4()),
            started_at=now_time,
            last_activity_at=now_time
        )
        self.sessions.append(new_session)
        self.current_session_id = new_session.session_id

    def close_current_session(self):
        self.get_current_session().closed_at = time.time()
        self.current_session_id = None

    def reset_runtime_state_for_new_session(self):
        self.active_task = None
        self.active_system_task = None
        self.focused_object = None
        self.paused_tasks = []

    def update_session_last_activity(self):
        self.get_current_session().last_activity_at = time.time()

    def begin_turn(self, user_message: UserMessage):
        self.pending_turn = Turn(
            turn_id=str(uuid.uuid4()),
            input_message=user_message
        )

    def fill_pending_turn(self, messages: List[BotMessage]):
        self.pending_turn.assistant_messages = messages

    def commit_pending_turn(self):
        self.get_current_session().turns.append(self.pending_turn)
        self.pending_turn = None

    #启动目标任务(定义上下文)
    def start_task(self,task_context: TaskContext):
        self.active_task = task_context
        self.active_system_task = None

    #启动系统任务
    def start_system_task(self,system_context: SystemContext):
        self.active_system_task = system_context

    #中断任务(若有正在进行的任务)
    def interrupt_active_task(self):
        self.paused_tasks.append(self.active_task)
        self.active_task = None
        self.active_system_task = None

    #填槽set_slots
    def set_slots(self,slots:dict):
        if self.active_task:
            self.active_task.slots.update(slots)

    #取消任务
    def cancel_active_task(self):
        self.active_task = None
        self.active_system_task = None

    #恢复任务
    def resume_task(self,flow_id:str):
        for task in self.paused_tasks:
            if task.flow_id == flow_id:
                self.active_task = task
                self.paused_tasks.remove(task)
                break


    def current_task(self)->TaskContext|SystemContext:
        return self.active_system_task or self.active_task

    def set_flow_next(self,target:str):
        self.current_task().step_id = target

    def end_system_task(self):
        self.active_system_task = None

    def end_task(self):
        self.active_task = None

    def set_focused_object(self, object: MessageObject):
        self.focused_object = FocusedObject(**object.to_dict())
