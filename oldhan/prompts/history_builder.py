from typing import List

from oldhan.domain.messages import UserMessage, MessageType, MessageObject, BotMessage
from oldhan.domain.state import Turn


#构建历史对话

def build_history(turns:List[Turn]):
    """
    构建历史对话内容，构建内容格式如下
    """
    chat_list = []
    for turn in turns:
        #一轮对话中用户消息
        user_message = turn.input_message
        #将用户的消息转换为要求的格式
        user_message_text = render_user_message(user_message) # user_message_text = "USER:[订单信息 ....]"
        chat_list.append(user_message_text)
        #一轮对话中机器消息
        bot_messages = turn.assistant_messages
        for bot_message in bot_messages:
            bot_message = render_bot_message(bot_message)# bot_message_text = "BOT:"
            chat_list.append(bot_message)
    return "\n".join(chat_list)

def render_bot_message(bot_message:BotMessage)->str:
    if bot_message.text:
        return f"BOT: {bot_message.text}"
    # 注意:这里要判 None。text 为空串或 None、且 object 也是 None 时,
    # 直接 render_object(None) 会 AttributeError: 'NoneType' object has no attribute 'type'
    if bot_message.object is not None:
        return f"BOT: {render_object(bot_message.object)}"
    return "BOT: (空消息)"



def render_user_message(user_message:UserMessage)->str:
    #判断UserMessage的类型是否是text
    if user_message.type == MessageType.TEXT:
        return f"USER: {user_message.text}"
    else:
        object:MessageObject = user_message.object
        if object is None:
            return "USER: (空消息)"
        # 这里原来漏了 return,导致对象消息渲染出来是 None
        object_text = render_object(object)
        return f"USER: {object_text}"



def render_object(object:MessageObject)->str:
    # [订单信息 id=ORD-20260620-88431,title=蓝牙耳机,status=已发货,amount=299.00,logistics=顺丰快递]
    # [商品信息 id=SKU-50012,title=索尼 WH-1000XM5,price=2499.00,type=头戴式,anc=行业领先]
    #判断object中是商品信息还是订单信息
    #[label]
    label = "订单信息" if object.type == "order" else "商品信息"
    #{
    #   "status": "已发货",
    #   "amount": 299.00,                   ===>  [“status=已发货”, “amount=299.00”, “logistics=顺丰快递”]
    #   "logistics":"顺丰快递"
    #}
    #  [“status=已发货”, “amount=299.00”, “logistics=顺丰快递”] ====>  "status=已发货,amount=299.00,logistics=顺丰快递"
    attributes_str = ",".join([f"{key}={value} "for key,value in object.attributes.items()])
    return f"[{label} id={object.id} title={object.title},{attributes_str}]"