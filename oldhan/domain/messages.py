from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


#领域模型
#定义用户消息类型
#继承 str 是为了能直接 json.dumps / 和 "text" 比较;只继承 Enum 时 json.dumps 会 TypeError
class MessageType(str, Enum):
    TEXT = "text"
    OBJECT = "object"

#定义对象消息模型
@dataclass(slots=True) #slots = True : 不能添加其他属性  (dataclass中默认值不可以为空[](BaseModel)-->field(default_factory=list))
class MessageObject:
    type : str
    id : str
    title : str
    attributes : dict[str,Any]

    #定义两个方法：to_dict-->转换为字典，from_dict-->转换为对象
     #data = asdict(obj)-->将对象转换为字典 obj = ClassInfo(**data)-->将字典转换为Info对象字典
    def to_dict(self)->dict:
        return asdict(self) #MessageObject中都是可转换对象可以直接转换

    @classmethod
    def from_dict(cls,dict_data)->"MessageObject":
        return cls(**dict_data)  #**dict_data把字典"":""解包为""=""

#定义用户消息模型
@dataclass(slots=True)
class UserMessage:
    sender_id : str  #消息者发送id
    message_id : str  #消息id
    type : MessageType
    text : str | None = None
    object : MessageObject | None = None

    def to_dict(self)->dict:
        return {
                "sender_id": self.sender_id,
                "message_id": self.message_id,
                "type":self.type.value,
                "text":self.text,
                "object":self.object.to_dict() if self.object else None
        }
    @classmethod
    def from_dict(cls,dict_data)->"UserMessage":
        return cls(
            sender_id = dict_data["sender_id"],
            message_id = dict_data["message_id"],
            type = MessageType.TEXT if dict_data["type"] == "text" else MessageType.OBJECT,
            # text 必须显式读出来!它有默认值 None,漏传不会报错,但用户说的话会静默丢失,
            # 导致 LLM 收到 "USER: None",意图识别只能判空
            text = dict_data.get("text"),
            object = MessageObject.from_dict(dict_data["object"]) if dict_data.get("object") else None
        )

#定义机器消息模型
@dataclass(slots=True)
class BotMessage:
    text : str | None = None
    object : MessageObject | None = None

    def to_dict(self)->dict:
        return {
            "text":self.text,
            # key 必须是小写 object,和 from_dict 读的对上(原来写成 "Object",往返后对象会丢)
            "object":self.object.to_dict() if self.object else None
        }
    @classmethod
    def from_dict(cls,dict_data)->"BotMessage":
        return cls(
            text = dict_data.get("text"),
            object = MessageObject.from_dict(dict_data["object"]) if dict_data.get("object") else None
        )

#定义Service处理结果模型
@dataclass(slots=True)
class ProcessResult:
    sender_id : str
    message_id : str #对哪条消息的回复
    messages : list[BotMessage] = field(default_factory=list)

    def to_dict(self)->dict:
        return {
            "sender_id": self.sender_id,
            "message_id": self.message_id,
            "messages": [message.to_dict() for message in self.messages]#取出message为BotMessage调用方法
        }

    @classmethod
    def from_dict(cls,dict_data)->"ProcessResult":
        return cls(
            sender_id = dict_data["sender_id"],
            message_id = dict_data["message_id"],
            messages = [BotMessage.from_dict(message_data) for message_data in dict_data["messages"]]
        )

