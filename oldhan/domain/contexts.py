from dataclasses import dataclass, field, asdict
from typing import Any, Dict


#定义上下文：用户上下文，系统上下文
#flow_id 任务流程：退款请求(一个flow含有多个step)
#step_id 每一个flow_id中的一个步骤
#slots 数据槽位(收集到信息：ask_order_number)


#用户上下文(将当前步骤查询到的内容放在slots中也就是任务上下文中,便于下一个step使用-->保存信息的)
@dataclass(slots=True)
class TaskContext:
    flow_id:str
    step_id:str
    slots:dict[str,Any] = field(default_factory=dict)

    def to_dict(self)->dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskContext":
        return cls(
            flow_id=data["flow_id"],
            step_id=data.get("step_id"),
            slots=dict(data.get("slots", {})),
        )


@dataclass(slots=True)
class SystemContext:
    """
    所有系统任务上下文的父类
    """
    flow_id:str
    step_id:str

    def to_dict(self)->dict:
        return {
            "flow_id": self.flow_id,
            "step_id": self.step_id,
        }

    @classmethod
    def from_dict(cls, raw_sys:Dict)->"SystemContext":
        flow_id = raw_sys.get("flow_id")
        return SYSTEM_CONTEXT_DICT[flow_id].from_dict(raw_sys)

@dataclass(slots=True)
class StartedSystemContext(SystemContext):
    """system_task_started系统任务的上下文"""
    started_flow_id:str
    started_flow_name:str

    def to_dict(self)->dict:
        return {
            "flow_id": self.flow_id,
            "step_id": self.step_id,
            "started_flow_id": self.started_flow_id,
            "started_flow_name": self.started_flow_name,
        }

    @classmethod
    def from_dict(cls, raw_sys:Dict)->"StartedSystemContext":
        return cls(
            flow_id=raw_sys["flow_id"],
            step_id=raw_sys["step_id"],
            started_flow_id=raw_sys["started_flow_id"],
            started_flow_name=raw_sys["started_flow_name"],
        )

@dataclass(slots=True)
class ResumedSystemContext(SystemContext):
    """system_task_resumed系统任务的上下文"""
    resumed_flow_id:str
    resumed_flow_name:str

    def to_dict(self)->dict:
        return {
            "flow_id": self.flow_id,
            "step_id": self.step_id,
            "resumed_flow_id": self.resumed_flow_id,
            "resumed_flow_name": self.resumed_flow_name,
        }

    @classmethod
    def from_dict(cls, raw_sys:Dict)->"ResumedSystemContext":
        return cls(
            flow_id=raw_sys["flow_id"],
            step_id=raw_sys["step_id"],
            resumed_flow_id=raw_sys["resumed_flow_id"],
            resumed_flow_name=raw_sys["resumed_flow_name"],
        )

@dataclass(slots=True)
class CannotHandleSystemContext(SystemContext):
    """system_cannot_handle系统任务的上下文"""
    reason:str
    def to_dict(self)->dict:
        return {
            "flow_id": self.flow_id,
            "step_id": self.step_id,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, raw_sys:Dict)->"CannotHandleSystemContext":
        return cls(
            flow_id=raw_sys["flow_id"],
            step_id=raw_sys["step_id"],
            reason=raw_sys["reason"],
        )

@dataclass(slots=True)
class CollectSystemContext(SystemContext):
    """system_collect_information系统任务上下文"""
    slot_name:str
    response:dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "flow_id": self.flow_id,
            "step_id": self.step_id,
            "slot_name": self.slot_name,
            "response": self.response,
        }

    @classmethod
    def from_dict(cls, raw_sys:Dict)->"CollectSystemContext":
        return cls(
            flow_id=raw_sys["flow_id"],
            step_id=raw_sys["step_id"],
            slot_name=raw_sys["slot_name"],
            response=raw_sys.get("response", {}),
        )

@dataclass(slots=True)
class InterruptedSystemContext(SystemContext):
    """system_task_interrupted系统任务上下文"""
    interrupted_flow_id:str
    interrupted_flow_name:str
    started_flow_id: str | None = None
    started_flow_name:str | None = None

    def to_dict(self)->dict:
        return {
            "flow_id": self.flow_id,
            "step_id": self.step_id,
            "interrupted_flow_id": self.interrupted_flow_id,
            "interrupted_flow_name": self.interrupted_flow_name,
            "started_flow_id": self.started_flow_id,
            "started_flow_name": self.started_flow_name,
        }


    @classmethod
    def from_dict(cls, raw_sys:Dict)->"InterruptedSystemContext":
        return cls(
            flow_id=raw_sys["flow_id"],
            step_id=raw_sys["step_id"],
            interrupted_flow_id=raw_sys["interrupted_flow_id"],
            interrupted_flow_name=raw_sys["interrupted_flow_name"],
            started_flow_id=raw_sys.get("started_flow_id"),
            started_flow_name=raw_sys.get("started_flow_name"),
        )

@dataclass(slots=True)
class CanceledSystemContext(SystemContext):
    """system_task_canceled系统任务上下文"""
    canceled_flow_id:str
    canceled_flow_name:str

    def to_dict(self)->dict:
        return {
            "flow_id": self.flow_id,
            "step_id": self.step_id,
            "canceled_flow_id": self.canceled_flow_id,
            "canceled_flow_name": self.canceled_flow_name,
        }

    @classmethod
    def from_dict(cls, raw_sys:Dict)->"CanceledSystemContext":
        return cls(
            flow_id=raw_sys["flow_id"],
            step_id=raw_sys["step_id"],
            canceled_flow_id=raw_sys["canceled_flow_id"],
            canceled_flow_name=raw_sys["canceled_flow_name"],
        )


SYSTEM_CONTEXT_DICT= {
    "system_task_started": StartedSystemContext,
    "system_task_resumed": ResumedSystemContext,
    "system_cannot_handle": CannotHandleSystemContext,
    "system_collect_information": CollectSystemContext,
    "system_task_interrupted": InterruptedSystemContext,
    "system_task_canceled": CanceledSystemContext,
}