#使用httpx创建http客户端(用于对电商后端接口发送http请求)

from httpx import AsyncClient

# 全局单例
http_client : AsyncClient | None = None

def init_http_client():
    global http_client
    http_client = AsyncClient()

async def close_http_client():
    await http_client.aclose()
