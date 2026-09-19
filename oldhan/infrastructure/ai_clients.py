#定义调用大模型客户端
from langchain.chat_models import init_chat_model

from oldhan.conf.config import  settings

llm_client = init_chat_model(
    model = settings.llm_model,
    model_provider = "openai",
    api_key = settings.llm_api_key,
    base_url = settings.llm_base_url,
    temperature = 0
)