#加载提示词
from pathlib import Path


def load_prompt(file_name:str):
    prompt_path = Path(__file__).parent /'jinja2'/f"{file_name}.jinja2"
    #必须显式写 encoding="utf-8":
    #  read_text() 不传 encoding 时用的是系统 locale 编码,Windows 中文环境下是 gbk,
    #  而 jinja2 模板是 UTF-8 存的中文 → UnicodeDecodeError: 'gbk' codec can't decode
    return prompt_path.read_text(encoding="utf-8")