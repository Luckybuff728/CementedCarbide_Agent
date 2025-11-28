"""
测试 LangSmith 追踪是否正常工作
"""
import asyncio
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

import os
print("=" * 50)
print("LangSmith 配置检查：")
print(f"  LANGSMITH_TRACING: {os.getenv('LANGSMITH_TRACING')}")
print(f"  LANGSMITH_PROJECT: {os.getenv('LANGSMITH_PROJECT')}")
print(f"  LANGSMITH_API_KEY: {os.getenv('LANGSMITH_API_KEY')[:20]}...")
print("=" * 50)

from src.agents.graph import get_conversational_manager

async def test():
    """发送测试消息并打印响应"""
    manager = get_conversational_manager()
    print("\n发送测试消息: '你好'\n")
    
    async for event in manager.chat('langsmith-test', '你好'):
        event_type = event.get('type')
        if event_type == 'token':
            print(event.get('content', ''), end='', flush=True)
        elif event_type == 'node_start':
            print(f"\n[节点开始: {event.get('node')}]")
        elif event_type == 'done':
            print("\n\n✓ 测试完成！请检查 LangSmith 网站")

if __name__ == "__main__":
    asyncio.run(test())
