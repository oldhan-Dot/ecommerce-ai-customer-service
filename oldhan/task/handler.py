from typing import List

from oldhan.domain.messages import BotMessage
from oldhan.domain.state import DialogueState
from oldhan.task.commands.models import Command
from oldhan.task.commands.processor import CommandProcessor
from oldhan.task.flows.executor import FlowExecutor
from oldhan.task.flows.models import FlowsList


class TaskHandler:

    def __init__(self,processor:CommandProcessor,executor:FlowExecutor,flowslist:FlowsList):
        self.processor = processor
        self.executor = executor
        self.flowslist = flowslist

    async def handle(self,commands:List[Command],state:DialogueState) -> List[BotMessage]:
        # 1.调用CommandProcessor组件进行命令处理
        self.processor.process_command(commands,state,self.flowslist)

        # 2.调用FlowExecutor进行流程推进,并返回生成的机器回复
        return await self.executor.run_task(state,self.flowslist)