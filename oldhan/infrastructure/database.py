#基于SQLALchemy框架进行数据的持久化访问(aiomysql)
#进行数据库的持久化操作需要session:AsyncSession对象
#session对象可以通过session_factory:async_sessionmaker类的实例来实现(工厂模式)
#创建工厂对象则需要engine:AsyncEngine来进行初始化
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, AsyncSession, create_async_engine

from oldhan.conf.config import settings

engine : AsyncEngine|None = None
session_factory : async_sessionmaker[AsyncSession]|None = None
def init_db_engine_and_session_factory():
    global engine, session_factory
    engine = create_async_engine(
        url = settings.database_url,
        echo = False, #是否打开日志
        pool_pre_ping = False, #是否打开预检查
    )
    session_factory = async_sessionmaker(
        engine,expire_on_commit = False, #是否在sql操作处理之后使ORM中的数据释放
    )
async def close_db_engine():
    if engine is not None:
        await engine.dispose()