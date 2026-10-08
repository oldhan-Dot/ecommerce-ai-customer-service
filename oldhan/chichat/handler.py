from typing import List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from oldhan.domain.messages import BotMessage
from oldhan.domain.state import DialogueState
from oldhan.infrastructure.ai_clients import llm_client
from oldhan.prompts.history_builder import build_history, render_user_message
from oldhan.prompts.prompt_loader import load_prompt


class ChitchatHandler:

    async def handle(self,state:DialogueState)->List[BotMessage]:
        # 1.获取用户对话状态中当前会话的历史记录
        turns = state.get_current_session().turns
        # 2.获取本轮对话的用户信息
        user_message = state.pending_turn.input_message
        # 3.加载提示词模板
        prompt_text = load_prompt("chichat_response")
        # 4.准备渲染参数
        prompt_inputs={
            "history":build_history(turns),
            "user_message":render_user_message(user_message),
        }
        # 5.调用LLM
        prompt = PromptTemplate.from_template(prompt_text,template_format="jinja2")
        chain = prompt | llm_client | StrOutputParser()
        respond = await chain.ainvoke(prompt_inputs)
        # 6.生成机器回复并返回
        return [BotMessage(text=respond)]