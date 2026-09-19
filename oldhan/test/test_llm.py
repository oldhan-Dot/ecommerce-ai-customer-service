from oldhan.infrastructure.ai_clients import llm_client

if __name__ == '__main__':
    response = llm_client.invoke("你是什么模型")
    print(response.content)