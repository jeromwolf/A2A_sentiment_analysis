"""
Analysis Agent V2 Adapter

기존 V1 분석 에이전트들(Sentiment, Score, Report)을 V2 프로토콜로 래핑하는 어댑터
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
import asyncio
import json
from typing import Dict, Any, List
from a2a_core.base.base_agent import BaseAgent
from a2a_core.protocols.message import A2AMessage, MessageType


class AnalysisAgentV2Adapter(BaseAgent):
    """V1 분석 에이전트를 V2로 래핑하는 어댑터"""
    
    def __init__(self, 
                 agent_type: str,
                 v1_port: int,
                 v2_port: int,
                 name: str,
                 description: str):
        super().__init__(
            name=name,
            description=description,
            port=v2_port,
            registry_url="http://localhost:8001"
        )
        
        self.agent_type = agent_type
        self.v1_port = v1_port
        self.v1_endpoint = f"http://localhost:{v1_port}"
        
    async def on_start(self):
        """에이전트 시작 시 초기화"""
        # 능력 등록
        capability_map = {
            "sentiment": {
                "name": "sentiment_analysis",
                "version": "2.0",
                "description": "수집된 데이터의 감정 분석",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "data": {"type": "array", "description": "분석할 데이터 배열"}
                    },
                    "required": ["data"]
                }
            },
            "score": {
                "name": "score_calculation", 
                "version": "2.0",
                "description": "감정 분석 결과를 바탕으로 점수 계산",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sentiments": {"type": "array", "description": "감정 분석 결과"}
                    },
                    "required": ["sentiments"]
                }
            },
            "report": {
                "name": "report_generation",
                "version": "2.0", 
                "description": "최종 투자 리포트 생성",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string", "description": "주식 티커"},
                        "query": {"type": "string", "description": "원본 질문"},
                        "score": {"type": "number", "description": "최종 점수"},
                        "sentiments": {"type": "array", "description": "감정 분석 결과"}
                    },
                    "required": ["ticker", "query", "score", "sentiments"]
                }
            }
        }
        
        if self.agent_type in capability_map:
            await self.register_capability(capability_map[self.agent_type])
            
        print(f"✅ {self.name} V2 어댑터 초기화 완료")
        
    async def on_stop(self):
        """에이전트 종료 시 정리"""
        print(f"🛑 {self.name} V2 어댑터 종료 중...")
        
    async def handle_message(self, message: A2AMessage):
        """메시지 처리"""
        try:
            if message.header.message_type == MessageType.REQUEST:
                action = message.body.get("action")
                
                if action == f"{self.agent_type}_analysis" or action == f"{self.agent_type}_calculation" or action == f"{self.agent_type}_generation":
                    await self._handle_analysis_request(message)
                else:
                    await self.reply_to_message(
                        message,
                        result={"error": f"Unsupported action: {action}"},
                        success=False
                    )
                    
        except Exception as e:
            print(f"❌ 메시지 처리 오류: {e}")
            import traceback
            traceback.print_exc()
            await self.reply_to_message(
                message,
                result={"error": str(e)},
                success=False
            )
            
    async def _handle_analysis_request(self, message: A2AMessage):
        """V1 에이전트로 분석 요청 전달"""
        payload = message.body.get("payload", {})
        
        print(f"📊 {self.name}: 분석 시작")
        print(f"📨 받은 페이로드: {json.dumps(payload, ensure_ascii=False)[:200]}...")
        
        try:
            # V1 에이전트가 실행 중인지 확인
            async with httpx.AsyncClient(timeout=5.0) as client:
                try:
                    health_check = await client.get(f"{self.v1_endpoint}/health")
                    if health_check.status_code != 200:
                        print(f"⚠️ V1 {self.agent_type} 에이전트가 응답하지 않음")
                except:
                    print(f"❌ V1 {self.agent_type} 에이전트에 연결할 수 없음")
                    
            # V1 에이전트 호출
            async with httpx.AsyncClient(timeout=60.0) as client:
                # 엔드포인트 및 데이터 매핑
                if self.agent_type == "sentiment":
                    # 감정 분석 요청
                    v1_payload = {
                        "data": payload.get("data", [])
                    }
                    response = await client.post(
                        f"{self.v1_endpoint}/analyze",
                        json=v1_payload
                    )
                    
                elif self.agent_type == "score":
                    # 점수 계산 요청
                    v1_payload = {
                        "sentiments": payload.get("sentiments", [])
                    }
                    response = await client.post(
                        f"{self.v1_endpoint}/calculate",
                        json=v1_payload
                    )
                    
                elif self.agent_type == "report":
                    # 리포트 생성 요청
                    v1_payload = {
                        "ticker": payload.get("ticker", ""),
                        "query": payload.get("query", ""),
                        "score": payload.get("score", 0),
                        "sentiments": payload.get("sentiments", [])
                    }
                    response = await client.post(
                        f"{self.v1_endpoint}/generate",
                        json=v1_payload
                    )
                
                print(f"📡 V1 응답 상태: {response.status_code}")
                
                if response.status_code == 200:
                    v1_data = response.json()
                    print(f"✅ V1 응답 받음: {json.dumps(v1_data, ensure_ascii=False)[:200]}...")
                    
                    # V2 형식으로 변환
                    result = self._convert_to_v2_format(v1_data)
                    
                    # 분석 완료 이벤트 브로드캐스트
                    await self.broadcast_event(
                        event_type=f"{self.agent_type}_completed",
                        event_data={
                            "type": self.agent_type,
                            "success": True
                        }
                    )
                    
                    await self.reply_to_message(message, result=result, success=True)
                else:
                    error_msg = f"V1 에이전트 오류: {response.status_code}"
                    error_detail = response.text
                    print(f"❌ {error_msg}: {error_detail}")
                    await self.reply_to_message(
                        message,
                        result={"error": error_msg, "detail": error_detail},
                        success=False
                    )
                    
        except Exception as e:
            print(f"❌ 분석 오류: {e}")
            import traceback
            traceback.print_exc()
            await self.reply_to_message(
                message,
                result={"error": str(e)},
                success=False
            )
            
    def _convert_to_v2_format(self, v1_data: Any) -> Dict:
        """V1 데이터를 V2 형식으로 변환"""
        if self.agent_type == "sentiment":
            # 감정 분석 결과 변환
            if isinstance(v1_data, list):
                return {
                    "sentiments": v1_data,
                    "count": len(v1_data),
                    "log_message": f"✅ {len(v1_data)}개 항목 감정 분석 완료"
                }
            else:
                return {
                    "sentiments": v1_data.get("sentiments", []),
                    "count": len(v1_data.get("sentiments", [])),
                    "log_message": "✅ 감정 분석 완료"
                }
                
        elif self.agent_type == "score":
            # 점수 계산 결과 변환
            return {
                "final_score": v1_data.get("final_score", 0),
                "details": v1_data.get("details", {}),
                "log_message": f"📊 최종 점수: {v1_data.get('final_score', 0):.1f}점"
            }
            
        elif self.agent_type == "report":
            # 리포트 생성 결과 변환
            return {
                "report": v1_data.get("report", ""),
                "summary": v1_data.get("summary", ""),
                "log_message": "📝 투자 리포트 생성 완료"
            }
            
        return v1_data


# 각 분석 타입별 어댑터 인스턴스 생성
def create_sentiment_adapter():
    return AnalysisAgentV2Adapter(
        agent_type="sentiment",
        v1_port=8002,
        v2_port=8202,
        name="Sentiment Analysis Agent V2",
        description="감정 분석을 수행하는 V2 에이전트"
    )

def create_score_adapter():
    return AnalysisAgentV2Adapter(
        agent_type="score",
        v1_port=8003,
        v2_port=8203,
        name="Score Calculation Agent V2",
        description="점수를 계산하는 V2 에이전트"
    )

def create_report_adapter():
    return AnalysisAgentV2Adapter(
        agent_type="report",
        v1_port=8004,
        v2_port=8204,
        name="Report Generation Agent V2",
        description="리포트를 생성하는 V2 에이전트"
    )


# FastAPI 앱 생성 함수들
def create_sentiment_app():
    agent = create_sentiment_adapter()
    app = agent.app
    
    @app.on_event("startup")
    async def startup():
        await agent.start()
        
    @app.on_event("shutdown")
    async def shutdown():
        await agent.stop()
        
    return app

def create_score_app():
    agent = create_score_adapter()
    app = agent.app
    
    @app.on_event("startup")
    async def startup():
        await agent.start()
        
    @app.on_event("shutdown")
    async def shutdown():
        await agent.stop()
        
    return app

def create_report_app():
    agent = create_report_adapter()
    app = agent.app
    
    @app.on_event("startup")
    async def startup():
        await agent.start()
        
    @app.on_event("shutdown")
    async def shutdown():
        await agent.stop()
        
    return app


# 독립 실행용
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python analysis_agent_v2_adapter.py [sentiment|score|report]")
        sys.exit(1)
        
    agent_type = sys.argv[1]
    
    if agent_type == "sentiment":
        agent = create_sentiment_adapter()
    elif agent_type == "score":
        agent = create_score_adapter()
    elif agent_type == "report":
        agent = create_report_adapter()
    else:
        print(f"Unknown agent type: {agent_type}")
        sys.exit(1)
        
    agent.run()