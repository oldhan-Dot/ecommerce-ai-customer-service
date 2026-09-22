from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file = Path(__file__).parents[2] / ".env",
        env_file_encoding = "utf-8",
        extra = "ignore", #可以忽视.env中不想添加的api
    )

    #LLM
    llm_api_key :str
    llm_base_url :str
    llm_model : str

    #数据库
    database_url :str

    #商城API
    commerce_api_base_url :str

    #服务器
    app_host :str
    app_port :int

settings = Settings()