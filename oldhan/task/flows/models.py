#================step的next属性  link===============
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict


@dataclass(slots=True)
class FlowStepLink:
    target : str

#if then
@dataclass(slots=True)
class ConditionalLink(FlowStepLink):
    condition : str


@dataclass(slots=True)
class FallbackLink(FlowStepLink):
    pass


@dataclass(slots=True)
class StaticLink(FlowStepLink):
    pass

#================flow下的steps属性===============

class FlowStepType(str, Enum):
    START = "start"
    ACTION = "action"
    COLLECT = "collect"
    END = "end"


@dataclass(slots=True)
class FlowStep:  #dict_data-->step_data
    id : str
    type : FlowStepType
    next : list[FlowStepLink]
    @classmethod
    def from_dict(cls,dict_data:dict)->"FlowStep":
        #这是一个工厂方法:按 type 找到具体的子类,把活儿交给它的 from_dict
        #不能写成 cls(子类.from_dict(...)) —— 那等于把一个造好的对象又当参数塞进构造函数
        return FLOWSTEP_DICT[dict_data.get("type")].from_dict(dict_data)


@dataclass(slots=True)
class StartFlowStep(FlowStep):
    @classmethod
    def from_dict(cls,dict_data:dict) -> "StartFlowStep":
        return cls(
            id = dict_data.get("id"),
            type = FlowStepType.START,
            next =_build_next_links(dict_data.get("next",[])
        ))

def _build_next_links(next_data:str|list)->list[FlowStepLink]:
    next_list = []
    if isinstance(next_data, str):
        next_list.append(StaticLink(target=next_data))
    else: #if then else
        for link_data in next_data:
            if link_data.get("if"):
                #注意:这里必须 append 到 next_list,不能 append 到 next_data
                #(next_data 是正在遍历的输入列表,往里加元素会让循环吃到刚加进去的对象)
                next_list.append(ConditionalLink(
                    condition=link_data.get("if"),
                    target=link_data.get("then")
                ))
            else:
                next_list.append(FallbackLink(
                    target=link_data.get("else")
                ))
    return next_list



@dataclass(slots=True)
class EndFlowStep(FlowStep):
    @classmethod
    def from_dict(cls,dict_data:dict) -> "ENDFlowStep":
        return cls(
            id = dict_data.get("id"),
            type = FlowStepType.END,
            next = []
        )

@dataclass(slots=True)
class ActionFlowStep(FlowStep):
    action : str
    args:Dict[str,Any] = field(default_factory=dict)
    @classmethod
    def from_dict(cls,dict_data:dict) -> "ActionFlowStep":
        return cls(
            id = dict_data.get("id"),
            type = FlowStepType.ACTION,
            next = _build_next_links(dict_data.get("next",[])),
            action = dict_data.get("action"),
            args = dict_data.get("args",{})
        )


#为什么定义ResponseDefine和SlotsValidation:多个值需要定义为一个类来封装
@dataclass(slots=True)
class ResponseDefinition:
    # mode 要给默认值:YAML 里大部分 collect 步骤只写 text,不写 mode
    # (取值为 static / rephrase / generate, 对应 ActionResponse 的三种渲染模式)
    mode : str = "static"
    text : str|None = None
    prompt : str|None = None

@dataclass(slots=True)
class SlotValidation:
    condition : str|None= None
    failure_response : ResponseDefinition | None= None

#收集信息
@dataclass(slots=True)
class CollectFlowStep(FlowStep):
    slot_name : str
    response : ResponseDefinition
    validation : SlotValidation | None = None
    @classmethod
    def from_dict(cls,dict_data:dict)->"CollectFlowStep":
        return cls(
            id = dict_data.get("id"),
            type = FlowStepType.COLLECT,
            next = _build_next_links(dict_data.get("next",[])),
            slot_name = dict_data.get("slot_name"), #collect流程是需要去收集信息，所有带有slot_name
            response = ResponseDefinition(**(dict_data.get("response") or {})),
            validation = SlotValidation(
                condition = dict_data.get("validation").get("condition"),
                failure_response=ResponseDefinition(**(dict_data.get("validation").get("failure_response") or {}))
            ) if dict_data.get("validation") else None,
        )






FLOWSTEP_DICT = {
    "start": StartFlowStep,
    "end": EndFlowStep,
    "action": ActionFlowStep,
    "collect": CollectFlowStep
}

#================flow===============

@dataclass(slots=True)
class FlowSlot:
    name : str
    type : str
    label : str
    description : str

@dataclass(slots=True)
class Flow:
    id : str
    name : str
    description : str
    steps : list[FlowStep] = field(default_factory=list)
    slot : list[FlowSlot] = field(default_factory=list)

    #根据type的类型在steps中获取到专属的step
    def get_start_step(self):
        for step in self.steps:
            if step.type == FlowStepType.START:
                return step
        raise Exception("No start step found in current flow")

    #根据 step_id 在 steps 中定位步骤(FlowExecutor 推进流程时要用)
    def get_step_by_id(self,step_id:str)->"FlowStep|None":
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

@dataclass(slots=True)
class FlowsList:
    slots : dict[str, FlowSlot] = field(default_factory=dict)
    flows : list[Flow] = field(default_factory=list)

    #通过flow_id从flows中获取目标flow
    def get_flow_by_id(self,flow_id:str)->Flow|None:
        for flow in self.flows:
            if flow.id == flow_id:
                return flow
        return None


