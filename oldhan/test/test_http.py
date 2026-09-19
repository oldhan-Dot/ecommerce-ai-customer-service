#测试http客户端
import asyncio

from oldhan.conf.config import  settings
from oldhan.infrastructure import http_util


async def test_http_client():
    http_util.init_http_client()
    result = await http_util.http_client.get(f'{settings.commerce_api_base_url}/users/u1001/orders')
    print(result.json())

    await http_util.close_http_client()
if __name__ == "__main__":
    asyncio.run(test_http_client())



