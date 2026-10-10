import time
import uuid
from typing import List
from oldhan.chitchat.handler import ChitchatHandler
from oldhan.clarify.reasons import ClarifyReason
from oldhan.clarify.responder import ClarifyResponder
from oldhan.domain.contexts import CollectSystemContext
from oldhan.domain.messages import BotMessage, MessageType, UserMessage, ProcessResult
from oldhan.domain.state import DialogueState
from oldhan.knowledge.handler import KnowledgeHandler
from oldhan.plan.models import TurnPlan, TaskTurnPlan
from oldhan.plan.planner import TurnPlanner
from oldhan.plan.validator import TurnPlanValidator
from oldhan.task.commands.models import SetSlotsCommand, Command
from oldhan.task.handler import TaskHandler


class DialogueEngine:
    def __init__(
            self,
            task_handler: TaskHandler,
            knowledge_handler: KnowledgeHandler,
            chitchat_handler: ChitchatHandler,
            turn_planner: TurnPlanner,
            turn_plan_validator: TurnPlanValidator,
            clarify_responder: ClarifyResponder
    ):
        self.task_handler = task_handler
        self.knowledge_handler = knowledge_handler
        self.chitchat_handler = chitchat_handler
        self.turn_planner = turn_planner
        self.turn_plan_validator = turn_plan_validator
        self.clarify_responder = clarify_responder

    async def process(self,user_message:UserMessage,state:DialogueState)->ProcessResult:
        # 1.准备会话
        self._prepare_session(state)

        # 2.创建本轮对话
        state.begin_turn(user_message)

        # 3.处理消息
        messages:List[BotMessage] = []
        if user_message.type == MessageType.TEXT:
            messages = await self._handle_text_message(user_message,state)
        else:
            messages = await self._handle_object_message(user_message,state)


        # 4.回填本轮对话：将消息处理之后产生的机器回复添加到本轮对话中
        state.fill_pending_turn(messages)

        # 5.将本轮对话提交到当前会话中
        state.commit_pending_turn()

        # 6.封装并返回处理结果
        return ProcessResult(
            sender_id=user_message.sender_id,
            message_id=user_message.message_id,
            messages= messages
        )

    def _prepare_session(self,state:DialogueState)->None:
        # - 从state中获取当前session：根据current_session_id从state的sessions中获取
        current_session = state.get_current_session()

        # - 如果 current_session 是 None ： 创建一个新的Session对象
        if current_session is None:
            state.start_session()
            return

        # - 如果 current_session 不是 None ：
        #        - 判断 current_session 有没有 “过期”
        if time.time() - current_session.last_activity_at > 60*60*2:
            # - 如果过期：
            # 关闭current_session
            state.close_current_session()
            # 重置state
            state.reset_runtime_state_for_new_session()
            # 创建一个新的Session对象
            state.start_session()
        else:
            # - 如果没有过期：继续使用current_session，更新last_activity_at时间戳
            state.update_session_last_activity()

    async def _handle_text_message(self, user_message: UserMessage, state: DialogueState) -> List[BotMessage]:
        # 1.意图识别
        turn_plan = await self.turn_planner.predict(self.task_handler.flowslist,
                                                    self.knowledge_handler.knowledge_intents, state)
        print(turn_plan)
        # 2.结构化命令校验
        validation_result = self.turn_plan_validator.validate(turn_plan, state,
                                                              self.knowledge_handler.knowledge_intents)
        # 3.轨道分发处理
        if validation_result.valid:
            if turn_plan.task is not None:
                messages = await self.task_handler.handle(turn_plan.task.commands, state)
            elif turn_plan.knowledge is not None:
                messages = await self.knowledge_handler.handle(turn_plan.knowledge.intents, state)
            else:
                messages = await self.chitchat_handler.handle(state)
        else:
            # 进行澄清
            messages = await self.clarify_responder.respond(state, validation_result.reason)
        return messages

    async def _handle_object_message(self, user_message: UserMessage, state: DialogueState) -> List[BotMessage]:
        # 1.将用户消息中的对象设置到state的focused_object(聚焦对象)
        state.set_focused_object(user_message.object)
        # 2.判断此对象是否用来为任务进行数据填槽，如果可以填槽，则生成填槽指令
        command: Command | None = None
        if state.active_task is not None and state.active_system_task is not None and isinstance(
                state.active_system_task, CollectSystemContext):
            if state.active_system_task.slot_name == "order_number" and user_message.object.type == "order":
                # 可以填槽，创建填槽指令
                command = SetSlotsCommand(
                    command="set_slots",
                    slots={
                        "order_number": user_message.object.id
                    }
                )
            if state.active_system_task.slot_name == "product_id" and user_message.object.type == "product":
                # 可以填槽，创建填槽指令
                command = SetSlotsCommand(
                    command="set_slots",
                    slots={
                        "product_id": user_message.object.id
                    }
                )
        # 3.判断command是否为None
        if command is not None:
            # 如果command不为None，则表示填槽成功，进入到任务轨道
            messages = await self.task_handler.handle([command], state)
        else:
            # 如果command为None，则表示填槽失败，进入到澄清轨道
            messages = await self.clarify_responder.respond(state, ClarifyReason.OBJECT_REQUIRES_INTENT)

        return messages

