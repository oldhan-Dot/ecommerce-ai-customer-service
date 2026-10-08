#加载提示词
from pathlib import Path


def load_prompt(file_name:str):
    prompt_path = Path(__file__).parent /'jinja2'/f"{file_name}.jinja2"
    return prompt_path.read_text()