import uuid

from fastapi import APIRouter, Depends

from oldhan.api.deps import get_dialogue_service
from oldhan.api.schemas import ChatHistoryMessageResponse, ChatHistoryResponse, ChatObjectPayload, ChatRequest, \
    ChatResponse, BotMessageResponse
from oldhan.domain.messages import UserMessage, ProcessResult
from oldhan.service.dialogue_service import DialogueService

router = APIRouter()

@router.get("/api/chat/history",response_model=ChatHistoryResponse)
async def chat_history(sender_id:str):
    print("sender_id :",sender_id)
    return ChatHistoryResponse(
        sender_id =sender_id,
        messages =[ChatHistoryMessageResponse(
            role = "user",
            text = "你好呀",
            object = None
        ),
        ChatHistoryMessageResponse(
            role = "user",
            object = ChatObjectPayload(
                type = "product",
                id = "l2026",
                title = "联想小新2026",
                attributes={
                    "color" : "green",
                    "price" : "6000.0",
                }
            )
        )

        ]
    )

@router.post("/api/chat") #对话接口
async def chat(chat_request:ChatRequest,
               dialogue_service:DialogueService = Depends(get_dialogue_service)):#依赖注入
    #1.将交互模型chat_request转换为领域模型UserMessage
     #模板
    dict_data = {
        "sender_id" : chat_request.sender_id,
        "message_id" : chat_request.message_id if chat_request.message_id else str(uuid.uuid4()),
        "type"  : "text" if chat_request.text else "object",
        "text" : chat_request.text,
        "object" : {
            "type":chat_request.object.type,
            "id":chat_request.object.id,
            "title":chat_request.object.title,
            "attributes":chat_request.object.attributes
        } if chat_request.object else None,
    }
     #用户消息
    user_message = UserMessage.from_dict(dict_data)
    #2.调用DialogueService类中的process_message方法进行对话处理
    process_result:ProcessResult = await DialogueService.process_message(user_message)

    #将领域模型process_result转换为交互模型ChatResponse
    messages = []
    for bot_message in process_result.messages:
        bot_message_response = BotMessageResponse(
            text = bot_message.text,
            object = ChatObjectPayload(
                type = bot_message.object.type,
                id = bot_message.object.id,
                title=bot_message.object.title,
                attributes=bot_message.object.attributes
            ) if bot_message.object is not None else None
        )
        messages.append(bot_message_response)
    chat_response = ChatResponse(
        sender_id = process_result.sender_id,
        message_id=process_result.message_id,
        messages = messages,
    )
    #4.返回交互模型 ChatResponse
    return chat_response

