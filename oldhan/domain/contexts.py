from dataclasses import dataclass, field
from typing import Any, Dict


#定义上下文：用户上下文，系统上下文
#flow_id 任务流程：退款请求(一个flow含有多个step)
#step_id 每一个flow_id中的一个步骤
#slots 数据槽位(收集到信息：ask_order_number)


#用户上下文(将当前步骤查询到的内容放在slots中也就是任务上下文中,便于下一个step使用-->保存信息的)
@dataclass(slots=True)
class TaskContext:
    flow_id: str
    step_id: str
    slots:dict[str,Any] = field(default_factory=dict) #记录拿到的内容：order_number....

    @classmethod
    def from_dict(cls,data:Dict[str, Any]) -> "TaskContext":
        return cls(
        flow_id = data["flow_id"],
        step_id = data["step_id"],
        slots = data.get("slots", {}),
        )

#系统上下文(是为用户上下文服务的:collect->执行系统任务)
@dataclass(slots=True)
class SystemContext:
    """
    所有系统任务的上下文的父类
    """
    flow_id: str
    step_id: str

    @classmethod
    def from_dict(cls,raw_sys:Dict[str, Any]) -> "SystemContext":
        flow_id = raw_sys.get("flow_id")
        return SYSTEM_CONTEXTS_DiICT[flow_id].from_dict(raw_sys)




#包括的任务 StartedSystemContext,ResumedSystemContext,CannotHandleSystemContext
#CollectSystemContext,InterruptSystemContext(先把当前放一放),Canceled SystemContext

@dataclass(slots=True)
class StartSystemContext(SystemContext):
    """system_task_started系统任务上下文"""
    start_flow_id: str
    start_step_name: str

    @classmethod
    def from_dict(cls,raw_sys:Dict[str, Any]) -> "StartSystemContext":
        return cls(
            flow_id = raw_sys["flow_id"],
            step_id = raw_sys["step_id"],
            start_flow_id = raw_sys["start_flow_id"],
            start_step_name = raw_sys["start_step_name"],
        )

@dataclass(slots=True)
class ResumedSystemContext(SystemContext):
    """system_task_resumed系统任务上下文"""
    resume_flow_id: str
    resume_step_name: str

    @classmethod
    def from_dict(cls,raw_sys:Dict[str, Any]) -> "ResumedSystemContext":
        return cls(
            flow_id = raw_sys["flow_id"],
            step_id = raw_sys["step_id"],
            resume_flow_id = raw_sys["resume_flow_id"],
            resume_step_name = raw_sys["resume_step_name"],

        )

@dataclass(slots=True)
class CannotHandleSystemContext(SystemContext):
    """system_cannot_handle系统任务上下文"""
    reason:str
    @classmethod
    def from_dict(cls,raw_sys:Dict[str, Any]) -> "CannotHandleSystemContext":
        return cls(
            flow_id = raw_sys["flow_id"],
            step_id = raw_sys["step_id"],
            reason = raw_sys["reason"],
        )

@dataclass(slots=True)
class CollectSystemContext(SystemContext):
    """system_collect_information系统任务上下文"""
    slot_name: str
    response:dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw_sys: Dict) -> "CollectSystemContext":
        return cls(
            flow_id=raw_sys["flow_id"],
            step_id=raw_sys["step_id"],
            slot_name=raw_sys["slot_name"],
            response=raw_sys.get("response", {}),
        )

@dataclass(slots=True)
class InterruptedSystemContext(SystemContext):
    """system_task_intertupted系统任务上下文"""
    interrupt_flow_id: str
    interrupt_step_name: str
    start_flow_id: str | None = None
    start_step_name: str | None = None

    @classmethod
    def from_dict(cls, raw_sys: Dict) -> "InterruptedSystemContext":
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
    """system_task_canceled上下文"""
    canned_flow_id: str
    canned_step_name: str

    @classmethod
    def from_dict(cls, raw_sys: Dict) -> "CanceledSystemContext":
        return cls(
            flow_id=raw_sys["flow_id"],
            step_id=raw_sys["step_id"],
            canceled_flow_id=raw_sys["canceled_flow_id"],
            canceled_flow_name=raw_sys["canceled_flow_name"],
        )
SYSTEM_CONTEXTS_DiICT = {
    "system_task_started": StartSystemContext,
    "system_task_resumed": ResumedSystemContext,
    "system_cannot_handle": CannotHandleSystemContext,
    "system_collect_information": CollectSystemContext,
    "system_task_interrupted": InterruptedSystemContext,
    "system_task_canceled": CanceledSystemContext,
}