from typing import Dict, Any
from pydantic import BaseModel
#交互模型    pydantic(类型转换和校验)

#历史会话
class ChatObjectPayload(BaseModel):
    type : str
    id : str
    title : str
    attributes:Dict[str,Any] = {} #Pydantic不支持any,要使用Any


class ChatHistoryMessageResponse(BaseModel):
    """历史记录中的一条消息"""
    session_id: str
    session_started_at: float
    role : str
    text : str| None = None
    object:ChatObjectPayload | None = None

class ChatHistoryResponse(BaseModel):#继承BaseModel后不需要__init__初始化(默认值可以写None)

    sender_id :str
    messages :list[ChatHistoryMessageResponse]

#对话
#接收用户发送的消息
class ChatRequest(BaseModel):
    sender_id : str
    text : str | None = None
    object:ChatObjectPayload | None = None
    message_id : str | None = None
#客服回复消息
class BotMessageResponse(BaseModel):
    """客户回复消息"""
    text : str | None = None
    object:ChatObjectPayload | None = None

class ChatResponse(BaseModel):
    sender_id : str
    message_id : str
    messages :list[BotMessageResponse]
