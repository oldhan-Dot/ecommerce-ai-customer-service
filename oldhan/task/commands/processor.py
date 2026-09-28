from pipes import stepkinds
from typing import List

from oldhan.domain.contexts import TaskContext, SystemContext, StartedSystemContext, InterruptedSystemContext, \
    CanceledSystemContext, ResumedSystemContext
from oldhan.domain.state import DialogueState
from oldhan.task.commands.models import Command, StartFlowCommand, SetSlotsCommand, CancelFlowCommand, ResumeFlowCommand
from oldhan.task.flows.models import FlowsList, Flow


#定义CommandProcessor

class CommandProcessor:
    #经过意图识别后，大模型将用户的自然语言根据提示词提取出json格式的命令文件,
    #task/commands/models中将传进来的command_dict转换为对象格式
    #转换为以下格式：
    #"请继续帮我完成退款"
    #commmands=[ResumeFlowCommand(command="resume_flow",flow="refund_request")]

    def process_command(self,commands:List[Command],state:DialogueState,flows_list:FlowsList) -> None:
        #遍历commands中的command,来匹配对应的Command对象
        for command in commands:
            if isinstance(command,StartFlowCommand):
                self._handle_start_flow(command,state,flows_list)
            elif isinstance(command,SetSlotsCommand):
                self._handle_set_slots(command,state)
            elif isinstance(command,CancelFlowCommand):
                self._handle_cancel_flow(command,state,flows_list)
            elif isinstance(command,ResumeFlowCommand):
                self._handle_resume_flow(command,state,flows_list)


    def _handle_start_flow(self,command:StartFlowCommand,state:DialogueState,flows_list:FlowsList):
        """
            StartFlowCommand(command=start_flow,flow="refund_request")
        """
        #1.获取目标Flow:从StateFlowCommand中获取flow_id,再根据flow_id从flows_list中获取到flow
        flow_id = command.flow
        target_flow:Flow = flows_list.get_flow_by_id(flow_id)#这里的Flow是定义的单个flow
        if target_flow:
            #2.判断是否有上下文
            current_task = state.active_task
            #3.判断是否有正在进行的任务
            if current_task:
                #有正在进行的任务
                state.interrupt_active_task()
                #启动目标任务
                state.start_task(TaskContext(
                    flow_id=flow_id,
                    step_id = target_flow.get_start_step().id,
                ))
                #启动任务上下文
                state.start_system_task(InterruptedSystemContext(
                    flow_id=flow_id,
                    step_id=flows_list.get_flow_by_id("system_task_interrupted").get_start_step().id,
                    interrupted_flow_id = current_task.flow_id,
                    interrupted_step_name=flows_list.get_flow_by_id(current_task.flow_id).name,
                    started_flow_id = flow_id,
                    started_flow_name=target_flow.name,
                ))
            else:
                #没有正在进行的用户任务，
                #启动目标任务(创建一个用户上下文)
                state.start_task(
                    TaskContext(
                        flow_id=flow_id,
                        step_id=target_flow.get_start_step().id  #启动
                    )
                )
                #启动system_task_started系统任务(创建系统上下文)
                state.start_system_task(StartedSystemContext(
                    flow_id="system_task_start",
                    step_id=flows_list.get_flow_by_id("system_task_start").get_start_step().id,
                    started_flow_id = flow_id,
                    started_flow_name = target_flow.name
                ))

    #填槽
    def _handle_set_slots(self,command:SetSlotsCommand,state:DialogueState):
        """
        SetSlotsCommand(command="set_slots",slots={"order_number":A20260011})
        """
        #1.从SetSlotsCommand中获取到slots
        slots = command.slots
        #2.(只要生成了set_slots指令,就一定有一个正在执行的用户任务)
        if state.active_task:
            state.set_slots(slots)

    #取消任务
    def  _handle_cancel_flow(self,command:CancelFlowCommand,state:DialogueState,flows_list:FlowsList):
        #1.从state中获取当前正在运行的用户任务上下文
        current_task = state.active_task
        if current_task:
            #2.取消当前任务
            state.cancel_active_task()
            #3.启动system_task_canceled系统任务(需要发出一句话)
            state.start_system_task(CanceledSystemContext(
                flow_id="system_task_canceled",
                step_id=flows_list.get_flow_by_id("system_task_canceled").get_start_step().id,
                canceled_flow_id=current_task.flow_id,
                canceled_flow_name=flows_list.get_flow_by_id(current_task.flow_id).name
            ))
    def _handle_resume_flow(self,command:ResumeFlowCommand,state:DialogueState,flows_list:FlowsList):
        """
        ResumeFlowCommand(command="resume_flow,flow="refund_request")
        """
        #1.获取目标flow
        target_flow_id = command.flow
        target_flow = flows_list.get_flow_by_id(target_flow_id)
        #2.获取任务上下文
        current_task = state.active_task
        #判断是否有正在执行的用户任务
        if current_task:
            #有正在执行的任务
            #挂起当前任务
            state.interrupt_active_task()
            #恢复目标任务
            state.resume_task(target_flow_id)
            #启动system_task_resumed系统任务
            state.start_system_task(InterruptedSystemContext(
                flow_id="system_task_resumed",
                step_id=flows_list.get_flow_by_id("system_task_resumed").get_start_step().id,
                interrupted_flow_id = current_task.flow_id,
                interrupted_flow_name=flows_list.get_flow_by_id(current_task.flow_id).name,
                started_flow_id = target_flow_id,
                started_flow_name=target_flow.name
            ))
        else:
            #没有正在执行的任务：直接恢复目标任务
            state.resume_task(target_flow_id)
            #启动系统任务
            state.start_system_task(ResumedSystemContext(
                flow_id="system_task_resumed",
                step_id=flows_list.get_flow_by_id("system_task_resumed").get_start_step().id,
                resumed_flow_id=target_flow_id,
                resumed_flow_name=target_flow.name
                )
            )

