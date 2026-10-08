from pathlib import Path

from oldhan.engine.dialogue_engine import DialogueEngine
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

    task_handler = TaskHandler(
        processor = CommandProcessor(),
        executor= FlowExecutor(
            runner = build_action_runner()
        ),
        flowslist = flows_list
    )

    return DialogueEngine(
        task_handler = task_handler
    )