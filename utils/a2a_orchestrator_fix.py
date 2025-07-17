"""
A2A 프로토콜 실제 사용을 위한 수정 코드
"""

from typing import Dict, Any
import asyncio
from common.a2a_base import BaseAgent, Message, MessageType, Priority

class A2ADataCollector:
    """A2A 메시지를 사용하여 데이터 수집"""
    
    def __init__(self, orchestrator: BaseAgent):
        self.orchestrator = orchestrator
        
    async def collect_data_via_a2a(self, session_id: str, ticker: str, exchange: str = "US"):
        """A2A 프로토콜을 사용한 데이터 수집"""
        
        # 거래소에 따른 에이전트 선택
        if exchange == "KRX":
            agents = ["news-agent", "twitter-agent", "dart-agent", "mcp-agent"]
        else:
            agents = ["news-agent", "twitter-agent", "sec-agent", "mcp-agent"]
        
        # 병렬 데이터 수집을 위한 태스크
        tasks = []
        
        for agent_id in agents:
            # A2A 메시지 생성
            message = await self.orchestrator.send_message(
                receiver_id=agent_id,
                action="collect_data",
                payload={"ticker": ticker},
                priority=Priority.HIGH,
                correlation_id=f"{session_id}-{agent_id}"
            )
            
            # 응답 대기 태스크 추가
            task = self._wait_for_response(message.header.message_id, agent_id)
            tasks.append(task)
        
        # 모든 응답 대기
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 결과 정리
        collected_data = {}
        for agent_id, result in zip(agents, results):
            if isinstance(result, Exception):
                print(f"❌ {agent_id} 데이터 수집 실패: {result}")
                collected_data[agent_id.replace("-agent", "")] = []
            else:
                collected_data[agent_id.replace("-agent", "")] = result.get("data", [])
        
        return collected_data
    
    async def _wait_for_response(self, message_id: str, agent_id: str, timeout: int = 60):
        """A2A 응답 대기"""
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            # 메시지 큐에서 응답 확인
            for msg in self.orchestrator.message_queue:
                if (msg.header.correlation_id == message_id and 
                    msg.header.sender_id == agent_id):
                    return msg.body
            
            await asyncio.sleep(0.1)
        
        raise TimeoutError(f"{agent_id}로부터 응답 시간 초과")


# main_orchestrator_v2.py의 _send_data_collection_request_http 메서드를 대체할 새 메서드
async def _send_data_collection_via_a2a(self, session: Dict, ticker: str):
    """A2A 프로토콜을 사용한 데이터 수집"""
    
    collector = A2ADataCollector(self)
    exchange = session.get("exchange", "US")
    session_id = session.get("session_id")
    
    # A2A 메시지로 데이터 수집
    collected_data = await collector.collect_data_via_a2a(session_id, ticker, exchange)
    
    # 세션에 데이터 저장
    session["collected_data"] = collected_data
    
    # UI 업데이트
    for data_type, data in collected_data.items():
        await self._send_to_ui(session.get("client_id"), "log", {
            "message": f"✅ {data_type.upper()} 데이터 수집 완료: {len(data)}건"
        })
    
    # 다음 단계로 진행
    session["state"] = "analyzing_sentiment"
    await self._start_sentiment_analysis(session)