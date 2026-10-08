from typing import List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from oldhan.clarify.reasons import ClarifyReason
from oldhan.domain.messages import BotMessage
from oldhan.domain.state import DialogueState
from oldhan.infrastructure.ai_clients import llm_client
from oldhan.prompts.history_builder import build_history, render_user_message
from oldhan.prompts.prompt_loader import load_prompt


class ClarifyResponder:

    async def respond(self, state: DialogueState, reason: ClarifyReason) -> List[BotMessage]:
        clarify_message = self.build_clarify_message(reason, state)
        # 加载提示词模板
        prompt_text = load_prompt("clarify_respond")
        # 提示词参数
        prompt_inputs = {
            "reason":reason.value,
            "clarify_message":clarify_message,
            "focused_object":state.focused_object,
            "history":build_history(state.get_current_session().turns),
            "user_message":render_user_message(state.pending_turn.input_message)
        }
        # 调用LLM
        prompt = PromptTemplate.from_template(
            prompt_text,
            template_format="jinja2"
        )
        chain = prompt | llm_client | StrOutputParser()
        rephrased_message = await chain.ainvoke(prompt_inputs)
        # 生成机器回复
        return [BotMessage(text=rephrased_message)]

    def build_clarify_message(self, reason: ClarifyReason, state: DialogueState) -> str:
        if reason is ClarifyReason.MULTIPLE_TRACKS:
            return "你这次同时提到了多个方向。我们先处理一个，你想先办业务还是先咨询信息呢？"
        if reason is ClarifyReason.MISSING_FOCUSED_OBJECT:
            return "请先发送你想咨询的商品或订单，我再继续帮你看。"
        if reason is ClarifyReason.MISSING_KNOWLEDGE_INTENT:
            return "你是想了解商品信息、订单信息，还是售后配送规则呢？"
        if reason is ClarifyReason.MISSING_TRACK:
            return "你是想先处理业务问题，还是先咨询信息呢？"
        if reason is ClarifyReason.MISSING_TASK_COMMANDS:
            return "你这次是想办理什么业务呢？比如查订单、查物流，或者申请退款。"
        if reason is ClarifyReason.OBJECT_REQUIRES_INTENT:
            focused_object = state.focused_object
            if focused_object is not None and focused_object.type == "order":
                return "我已经收到这个订单了。你想查订单状态、查物流，还是申请退款呢？"
            if focused_object is not None and focused_object.type == "product":
                return "我已经收到这个商品了。你想了解它的商品信息、发货情况，还是售后相关问题呢？"
        return "我还需要再确认一下你的意思，你可以换个更具体的说法告诉我。"