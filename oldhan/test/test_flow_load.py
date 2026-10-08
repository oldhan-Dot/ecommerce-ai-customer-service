from pathlib import Path

from oldhan.task.flows.loader import FlowLoader

if __name__ == '__main__':
    user_flows_path = Path(__file__).parents[2] / "flow_config/user_flows.yml"
    loader = FlowLoader()
    flows_list = loader.load(user_flows_path)
    print(flows_list)
