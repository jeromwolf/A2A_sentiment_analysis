#!/usr/bin/env python3
"""
확장성 테스트용 새로운 에이전트
BaseAgent를 상속받아 간단한 기능만 구현
"""

from a2a_core.base.base_agent import BaseAgent
from a2a_core.protocols.message import A2AMessage, MessageType
import logging
from typing import Dict, Any
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestScalabilityAgent(BaseAgent):
    """확장성 테스트를 위한 간단한 에이전트"""
    
    def __init__(self):
        super().__init__(
            name="Test Scalability Agent",
            description="A2A 시스템의 확장성을 테스트하는 에이전트",
            port=8999  # 새로운 포트 사용
        )
        
        # 간단한 상태 저장
        self.request_count = 0
        
    async def on_start(self):
        """에이전트 시작 시 호출"""
        # 능력 등록
        await self.register_capability({
            "name": "echo_test",
            "version": "1.0",
            "description": "메시지를 받아서 에코 응답",
            "input_schema": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "에코할 메시지"}
                },
                "required": ["message"]
            }
        })
        
        await self.register_capability({
            "name": "status_check",
            "version": "1.0",
            "description": "에이전트 상태 확인",
            "input_schema": {
                "type": "object",
                "properties": {}
            }
        })
        
        logger.info(f"✅ {self.name} 초기화 완료 - 능력 등록 완료")
        
    async def on_stop(self):
        """에이전트 종료 시 호출"""
        logger.info(f"👋 {self.name} 종료 - 총 {self.request_count}개 요청 처리")
        
    async def handle_message(self, message: A2AMessage):
        """메시지 처리"""
        logger.info(f"📨 메시지 수신 - Type: {message.header.message_type}, Action: {message.body.get('action')}")
        
        if message.header.message_type == MessageType.REQUEST:
            action = message.body.get("action")
            
            if action == "echo_test":
                await self._handle_echo_test(message)
            elif action == "status_check":
                await self._handle_status_check(message)
            else:
                await self.reply_to_message(
                    message, 
                    {"error": f"Unknown action: {action}"}, 
                    success=False
                )
                
    async def _handle_echo_test(self, message: A2AMessage):
        """에코 테스트 처리"""
        try:
            self.request_count += 1
            payload = message.body.get("payload", {})
            echo_message = payload.get("message", "")
            
            result = {
                "original_message": echo_message,
                "echo": f"Echo from {self.name}: {echo_message}",
                "timestamp": datetime.now().isoformat(),
                "request_number": self.request_count
            }
            
            logger.info(f"✅ Echo 처리 완료: {echo_message}")
            await self.reply_to_message(message, result, success=True)
            
        except Exception as e:
            logger.error(f"❌ Echo 처리 중 오류: {e}")
            await self.reply_to_message(
                message,
                {"error": str(e)},
                success=False
            )
            
    async def _handle_status_check(self, message: A2AMessage):
        """상태 확인 처리"""
        try:
            status = {
                "agent_name": self.name,
                "agent_id": self.agent_id,
                "status": "active",
                "request_count": self.request_count,
                "capabilities": [cap["name"] for cap in self.capabilities],
                "uptime": datetime.now().isoformat()
            }
            
            logger.info(f"✅ 상태 확인 응답")
            await self.reply_to_message(message, status, success=True)
            
        except Exception as e:
            logger.error(f"❌ 상태 확인 중 오류: {e}")
            await self.reply_to_message(
                message,
                {"error": str(e)},
                success=False
            )


# 에이전트 인스턴스 생성
agent = TestScalabilityAgent()

# BaseAgent의 app을 사용
app = agent.app

if __name__ == "__main__":
    import uvicorn
    # agent.run() 대신 직접 uvicorn 실행
    uvicorn.run(app, host="0.0.0.0", port=8999)