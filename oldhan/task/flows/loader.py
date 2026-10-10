from pathlib import Path

import yaml

from oldhan.task.flows.models import FlowsList, FlowSlot, Flow, FlowStep, CollectFlowStep

#通过task/flows/models文件中的类将yml文件--->传入step_data转换为对象格式
class FlowLoader:

    def load_many(self, paths: list[Path])->FlowsList:
        slots = {}
        flows = []
        for path in paths:
            flowslist = self.load(path)
            slots.update(flowslist.slots)
            flows.extend(flowslist.flows)
        return FlowsList(slots=slots,flows=flows)

    def load(self,path:Path)->FlowsList:
        with open(path,"r",encoding="utf-8") as f:
            data  = yaml.safe_load(f)
            #获取yaml中的slots数据
            #注意:system_flows.yml 里没有 slots 段,data.get 会返回 None,所以兜底成空字典
            slots_data = data.get("slots") or {}
            #解析slots数据
            slots = self._load_slots(slots_data)

            #获取yaml中的flows数据
            flows_data = data.get("flows") or {}
            #解析flows数据(把已经解析好的 slots 传进去,flow 要用它反查自己需要的槽位)
            flows = self._load_flows(flows_data, slots)
            return FlowsList(
                slots=slots,
                flows=flows
            )




    #解析slots数据为以slot_name为键,FlowSlot为值
    def _load_slots(self,slots_data:dict)->dict[str, FlowSlot]:
        slots = {}
        for slot_name,slot_data in slots_data.items():
            slots[slot_name] = FlowSlot(name=slot_name,**slot_data)
        return slots

    def _load_flows(self,flows_data:dict,slots : dict[str,FlowSlot])->list[Flow]:
        flows = []
        for flow_id,flow_data in flows_data.items():
            flow_name = flow_data.get("name")
            flow_description = flow_data.get("description")
            #解析flows中的steps
            steps = [FlowStep.from_dict(step_data) for step_data in flow_data.get("steps")]
            #获取当前flow所需的槽位
            flow_slots = []
            for step in steps:
                if isinstance(step,CollectFlowStep):
                    flow_slot : FlowSlot = slots.get(step.slot_name)
                    #槽位表里没有这个名字就跳过,避免把 None 塞进列表
                    if flow_slot is not None:
                        flow_slots.append(flow_slot)


            flows.append(Flow(
                id=flow_id,
                name=flow_name,
                description=flow_description,
                steps=steps,
                slot=flow_slots
            ))
        return flows