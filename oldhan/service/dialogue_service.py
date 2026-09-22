from oldhan.domain.messages import UserMessage, ProcessResult, BotMessage, MessageObject


#定义消息处理方法(暂时跳过消息过程,返回要给的固定的消息)
class DialogueService:

    def process_message(self,user_message:UserMessage)->ProcessResult:
        #1.调用Repository层：根据message.sender_id查询当前用户的对话状态
        #2.调用Engine层：处理消息
        #3.调用Repository层：更新对话状态
        #4.返回处理结果
        return ProcessResult(
            sender_id = user_message.sender_id,
            message_id = user_message.message_id,
            messages = [
                BotMessage(
                    text = "你好，我是小韩，有什么为你服务的",
                    object = None
                ),
                BotMessage(
                    text = None,
                    object = MessageObject(
                        type = "product",
                        id = "12345",
                        title = "戴尔电脑",
                        attributes={
                            "size":"1000G",
                            "color":"white",
                            "price":"5666.8"
                        }
                    )
                )
            ]
        )