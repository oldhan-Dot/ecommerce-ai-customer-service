from pathlib import Path

from oldhan.chichat.handler import ChitchatHandler
from oldhan.clarify.responder import ClarifyResponder
from oldhan.engine.dialogue_engine import DialogueEngine
from oldhan.knowledge.handler import KnowledgeHandler
from oldhan.knowledge.intents import KNOWLEDGE_INTENTS
from oldhan.knowledge.providers import OrderAPIProvider, ProductAPIProvider, FAQProvider, RAGProvider
from oldhan.knowledge.registry import KnowledgeProviderRegistry
from oldhan.knowledge.responder import KnowledgeResponder
from oldhan.plan.planner import TurnPlanner
from oldhan.plan.validator import TurnPlanValidator
from oldhan.task.action.builder import build_action_runner
from oldhan.task.commands.processor import CommandProcessor
from oldhan.task.flows.executor import FlowExecutor
from oldhan.task.flows.loader import FlowLoader
from oldhan.task.handler import TaskHandler


def build_dialogue_engine()->DialogueEngine:
    user_flows_path = Path(__file__).parents[2] / 'flow_config' / 'user_flows.yml'
    system_flows_path = Path(__file__).parents[2] / 'flow_config' / 'system_flows.yml'
    loader = FlowLoader()
    flows_list = loader.load_many([user_flows_path, system_flows_path])

    # 1.创建TaskHandler实例
    task_handler = TaskHandler(
        processor=CommandProcessor(),
        executor=FlowExecutor(
            runner=build_action_runner()
        ),
        flowslist=flows_list
    )

    # 2.创建KnowledgeHandler实例
    knowledge_handler = KnowledgeHandler(
        knowledge_intents=KNOWLEDGE_INTENTS,
        provider_registry=KnowledgeProviderRegistry([
            ProductAPIProvider(),
            OrderAPIProvider(),
            FAQProvider(),
            RAGProvider()
        ]),
        knowledge_responder=KnowledgeResponder()
    )

    # 3.创建ChitchatHandler实例
    chitchat_handler = ChitchatHandler()

    # 4.创建TurnPlanner实例
    turn_planner = TurnPlanner()

    # 5.创建TurnPlanValidator
    turn_plan_validator = TurnPlanValidator()

    # 6.创建ClarifyResponder
    clarify_responder = ClarifyResponder()

    # 创建DialogueEngine实例
    return DialogueEngine(
        task_handler=task_handler,
        knowledge_handler=knowledge_handler,
        chitchat_handler=chitchat_handler,
        turn_planner=turn_planner,
        turn_plan_validator=turn_plan_validator,
        clarify_responder=clarify_responder
    )