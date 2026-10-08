from dataclasses import asdict
from typing import List

from oldhan.domain.contexts import SystemContext, CollectSystemContext, TaskContext
from oldhan.domain.messages import BotMessage
from oldhan.domain.state import DialogueState
from oldhan.task.action.builtin import action_listen
from oldhan.task.action.runner import ActionCall, ActionRunner
from oldhan.task.flows.models import FlowsList, ActionFlowStep, CollectFlowStep, ConditionalLink, StaticLink, FlowStep, \
    StartFlowStep, EndFlowStep, Flow, FlowStepLink


class FlowExecutor:

    def __init__(self,runner:ActionRunner):
        self.runner = runner

    async def run_task(self,state:DialogueState, flowslist:FlowsList)->List[BotMessage]:
        """外层循环"""
        messages:List[BotMessage] = []
        while True:
            # 1.调用内层循环推进流程，获取ActionCall
            action_call = self.advance_until_action(state, flowslist)
            # 2.判断action_call中的action_name是否action_listen
            if action_call.action_name == "action_listen":
                break
            # 3.调用ActionRunner执行Action,获取Action执行的结果 ActionResult
            action_result = await self.runner.execute_action(action_call, state)
            # 4.将ActionResult的messages设置到messages中
            #    将slot_updates中的数据设置到state用户上下文槽位中
            messages.extend(action_result.messages)
            state.set_slots(action_result.slot_updates)
        return messages

    def advance_until_action(self,state:DialogueState, flowslist:FlowsList)->ActionCall:
        """内层循环"""
        while True:
            current_task: TaskContext|SystemContext = state.current_task()
            if current_task is None:
                return ActionCall(
                    action_name="action_listen"
                )
            print(f"~~~~~~~~~~~~~~~{current_task.flow_id}~~~~~~~~~~~~{current_task.step_id}")
            # 获取任务中的flow和step
            flow:Flow = flowslist.get_flow_by_id(current_task.flow_id)
            step:FlowStep = flow.get_step_by_id(current_task.step_id)
            # 判断step类型
            if isinstance(step,StartFlowStep):
                self._run_start_step(step,state)
            elif isinstance(step,EndFlowStep):
                self._run_end_step(state)
            elif isinstance(step,ActionFlowStep):
                return self._run_action_step(step,state)
            elif isinstance(step,CollectFlowStep):
                action_call:ActionCall|None = self._run_collect_step(step,state,flowslist)
                if action_call:
                    return action_call

    def _run_start_step(self, step:StartFlowStep, state:DialogueState)->None:
        # 将step的next，设置到 state中当前任务上下文的 step_id
        target = self.get_step_next_target(step,state)
        state.set_flow_next(target)

    def get_step_next_target(self,step:FlowStep,state:DialogueState)->str:
        next_list: list[FlowStepLink] = step.next
        for next_link in next_list:
            if isinstance(next_link, StaticLink):
                return next_link.target
            elif isinstance(next_link, ConditionalLink):
                condition = next_link.condition  # "context.reason == 'clarification_rejected'"
                globals = {"__builtins__": {}}
                locals = {
                    "slots": state.active_task.slots if state.active_task is not None else {},
                    "context": state.active_system_task.to_dict() if state.active_system_task is not None else {}
                }
                # eval(expression, globals, locals)
                # expression ： 要执行的字符串类型的条件表达式
                # globals : {"__builtins__": {}} 全局命名空间
                # locals : 本地变量，expression表达式可以访问locals中的变量
                if bool(eval(condition, globals, locals)):
                    return next_link.target
            else:
                return next_link.target

    def _run_end_step(self, state:DialogueState)->None:
        current_task = state.current_task()
        if isinstance(current_task, SystemContext):
            state.end_system_task()
        else:
            state.end_task()

    def _run_action_step(self, step:ActionFlowStep, state:DialogueState)->ActionCall:
        # 1.将流程推进到下一步
        target = self.get_step_next_target(step,state)
        state.set_flow_next(target)
        # 2.返回当前Action对应的ActionCall
        if isinstance(step.args, dict):
            return ActionCall(
                action_name=step.action,
                action_args= step.args
            )
        elif isinstance(step.args, str):
            # 如果 args 是字符串类型  （context.response）,表示要从任务上下文中获取参数
            args = state.current_task().to_dict()[step.args.split(".")[1]]   #  "response"
            return ActionCall(
                action_name=step.action,
                action_args= args
            )
        else:
            return ActionCall(
                action_name=step.action,
                action_args= {}
            )

    def _run_collect_step(self, step:CollectFlowStep, state:DialogueState, flowslist:FlowsList)->ActionCall|None:
        # 1.尝试自动填槽
        if state.focused_object is not None:
            if step.slot_name == "order_number" and state.focused_object.type == "order":
                state.set_slots({
                    "order_number": state.focused_object.id
                })
            if step.slot_name == "product_id" and state.focused_object.type == "product":
                state.set_slots({
                    "product_id": state.focused_object.id
                })
        # 2.判断槽位是否有值
        if state.active_task.slots.get(step.slot_name) is None:
            # 如果用户任务上下文的数据槽位中没有当前 step收集的数据
            state.start_system_task(CollectSystemContext(
                flow_id= "system_collect_information",
                step_id= flowslist.get_flow_by_id("system_collect_information").get_start_step().id,
                slot_name=step.slot_name,
                response= asdict(step.response)
            ))
        else:
            # 如果用户任务上下文的数据槽位中有当前 step收集的数据
            if step.validation is None:
                # 没有验证条件：将流程推进到下一步
                target = self.get_step_next_target(step,state)
                state.set_flow_next(target)
            else:
                # 有校验条件
                condition = step.validation.condition
                globals = {"__builtins__": {}}
                locals = {
                    "slots": state.active_task.slots if state.active_task is not None else {},
                    "context": state.active_system_task.to_dict() if state.active_system_task is not None else {}
                }
                if bool(eval(condition, globals, locals)):
                    # 通过校验
                    target = self.get_step_next_target(step, state)
                    state.set_flow_next(target)
                else:
                    # 未通过校验：清除上下文slots中的当前槽位数据（step.slot_name）
                    state.set_slots({
                        step.slot_name: None
                    })
                    # 判断是否有校验不通过的失败提示
                    if step.validation.failure_response is not None:
                        return ActionCall(
                            action_name="action_response",
                            action_args=asdict(step.validation.failure_response)
                        )
