from oldhan.domain.messages import UserMessage, ProcessResult, BotMessage, MessageObject
from oldhan.domain.state import DialogueState
from oldhan.engine.dialogue_engine import DialogueEngine
from oldhan.repository.dialogue_state_repository import DialogueStateRepository


#定义消息处理方法(暂时跳过消息过程,返回要给的固定的消息)
class DialogueService:

    def __init__(self, repository: DialogueStateRepository, engine: DialogueEngine):
        self.repository = repository
        self.engine = engine

    async def process_message(self, user_message: UserMessage) -> ProcessResult:
        # 1.调用Repository层：根据message.sender_id查询当前用户的对话状态
        state: DialogueState = await self.repository.load(user_message.sender_id)

        # 2.调用Enginge层：处理消息  async def process(user_message,state)->ProcessResult
        process_result: ProcessResult = await self.engine.process(user_message, state)

        # 3.调用Repository层：更新对话状态
        await self.repository.save(state)

        # 4.返回处理结果
        return process_result