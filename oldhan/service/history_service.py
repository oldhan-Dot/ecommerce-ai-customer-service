from oldhan.api.schemas import ChatHistoryMessageResponse, ChatObjectPayload
from oldhan.domain.state import DialogueState
from oldhan.repository.dialogue_state_repository import DialogueStateRepository


class HistoryService:
    def __init__(self,repository:DialogueStateRepository):
        self.repository = repository

    async def list_history(self,sender_id:str)->list[ChatHistoryMessageResponse]:
        #从持久化存储中 加载用户的状态
        state:DialogueState = await self.repository.load(sender_id)

        messages:list[ChatHistoryMessageResponse]=[]
        for session in state.sessions:
            session_id = session.session_id
            started_at = session.started_at
            turns = session.turns
            for turn in turns:
                # 用户消息
                user_message = turn.input_message
                messages.append(
                    ChatHistoryMessageResponse(
                        role="user",
                        session_id=session_id,
                        session_started_at=started_at,
                        text=user_message.text,
                        object=ChatObjectPayload(
                            type=user_message.object.type,
                            id=user_message.object.id,
                            title=user_message.object.title,
                            attributes=user_message.object.attributes
                        ) if user_message.object is not None else None
                    )
                )
                # 客服消息（机器消息）
                bot_messages = turn.assistant_messages
                for bot_message in bot_messages:
                    messages.append(
                        ChatHistoryMessageResponse(
                            role="bot",
                            session_id=session_id,
                            session_started_at=started_at,
                            text=bot_message.text,
                            object=ChatObjectPayload(
                                type=bot_message.object.type,
                                id=bot_message.object.id,
                                title=bot_message.object.title,
                                attributes=bot_message.object.attributes
                            ) if bot_message.object is not None else None
                        )
                    )
        return messages