import json
from dataclasses import asdict

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

from oldhan.domain.state import DialogueState
from oldhan.infrastructure.ai_clients import llm_client
from oldhan.knowledge.intents import KnowledgeIntent
from oldhan.plan.models import TurnPlan
from oldhan.prompts.history_builder import build_history, render_user_message
from oldhan.prompts.prompt_loader import load_prompt
from oldhan.task.flows.models import FlowsList


#意图识别


class TurnPlanner:

    async def predict(
            self,
            flowslist:FlowsList,
            knowledge_intents:dict[str,KnowledgeIntent],
            state:DialogueState,
    )->TurnPlan:

        #1.加载提示词模板
        prompt_text = load_prompt("turn_plan")
        #2.构造提示词参数
        #flow信息
        flows_info = [{k:v for k,v in asdict(flow).items() if k!="steps"} for flow in flowslist.flows]
        #knowledge_intents信息
        knowledge_intents_info = [{"id":intent.id,"description":intent.description}for intent in knowledge_intents.values()]
        prompt_inputs = {
            "available_flows_json": json.dumps({"flows": flows_info}, ensure_ascii=False),
            "knowledge_intents_json": json.dumps(knowledge_intents_info, ensure_ascii=False),
            "active_task_json": json.dumps(asdict(state.active_task) if state.active_task else None,
                                           ensure_ascii=False),
            "interrupted_tasks_json": json.dumps([asdict(task) for task in state.paused_tasks], ensure_ascii=False),
            "focused_object_json": json.dumps(asdict(state.focused_object) if state.focused_object else None,
                                              ensure_ascii=False),
            "current_conversation": build_history(state.get_current_session().turns),
            "user_message": render_user_message(state.pending_turn.input_message)
        }
        #3.调用llm
        prompt = PromptTemplate.from_template(
            prompt_text,
            template_format="jinja2",
        )
        chain = prompt | llm_client | JsonOutputParser()
        result = await chain.ainvoke(prompt_inputs)
        #4.将大模型返回的Json对象，转换为TurnPlan
        return TurnPlan.from_dict(result)