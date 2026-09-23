from sqlalchemy import String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped
from sqlalchemy.testing.schema import mapped_column


#定义数据库记录状态

class Base(DeclarativeBase):
    pass


class DialogueStateRecord(Base):
    """dialogue_states 表：每个用户一行, state_json:存储完整的对话状态"""
    __tablename__ = 'dialogue_states'
    sender_id : Mapped[str] = mapped_column( String(255),primary_key=True)
    state_json: Mapped[str] = mapped_column(Text,nullable=False,default="{}")
