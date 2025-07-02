"""
Twitter Agent V2 - V1 Twitter Agent를 V2 프로토콜로 래핑
"""

from agents.data_agent_v2_adapter import create_twitter_app

# uvicorn이 찾을 수 있도록 app 객체 생성
app = create_twitter_app()