import time
import uuid
from typing import List

from oldhan.domain.messages import BotMessage, MessageType, UserMessage, ProcessResult
from oldhan.domain.state import DialogueState


class DialogueEngine:

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

    async def _handle_text_message(self,user_message:UserMessage,state:DialogueState)->List[BotMessage]:

        return [BotMessage(text="文本消息处理的机器回复")]

    async def _handle_object_message(self,user_message:UserMessage,state:DialogueState)->List[BotMessage]:

        return [BotMessage(text="对象消息处理的机器回复")]
