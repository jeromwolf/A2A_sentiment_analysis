"""
Data Collection Agent V2 Adapter

기존 V1 데이터 수집 에이전트들을 V2 프로토콜로 래핑하는 어댑터
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
import asyncio
from typing import Dict, Any, List
from a2a_core.base.base_agent import BaseAgent
from a2a_core.protocols.message import A2AMessage, MessageType


class DataAgentV2Adapter(BaseAgent):
    """V1 데이터 수집 에이전트를 V2로 래핑하는 어댑터"""
    
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
            "news": {
                "name": "news_data_collection",
                "version": "2.0",
                "description": "뉴스 데이터 수집",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string", "description": "주식 티커"}
                    },
                    "required": ["ticker"]
                }
            },
            "twitter": {
                "name": "twitter_data_collection", 
                "version": "2.0",
                "description": "트위터 데이터 수집",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string", "description": "주식 티커"}
                    },
                    "required": ["ticker"]
                }
            },
            "sec": {
                "name": "sec_data_collection",
                "version": "2.0", 
                "description": "SEC 공시 데이터 수집",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string", "description": "주식 티커"}
                    },
                    "required": ["ticker"]
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
                
                if action == f"{self.agent_type}_data_collection":
                    await self._handle_collect_data(message)
                else:
                    await self.reply_to_message(
                        message,
                        result={"error": f"Unsupported action: {action}"},
                        success=False
                    )
                    
        except Exception as e:
            print(f"❌ 메시지 처리 오류: {e}")
            await self.reply_to_message(
                message,
                result={"error": str(e)},
                success=False
            )
            
    async def _handle_collect_data(self, message: A2AMessage):
        """V1 에이전트로 데이터 수집 요청 전달"""
        payload = message.body.get("payload", {})
        ticker = payload.get("ticker", "")
        
        print(f"📊 {self.name}: {ticker} 데이터 수집 시작")
        
        # V1 에이전트 가용성 체크
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                health_check = await client.get(f"{self.v1_endpoint}/docs")
                if health_check.status_code != 200:
                    print(f"⚠️ V1 {self.agent_type} 에이전트가 응답하지 않습니다 (port {self.v1_port})")
        except:
            print(f"⚠️ V1 {self.agent_type} 에이전트에 연결할 수 없습니다 (port {self.v1_port})")
        
        try:
            # V1 에이전트 호출
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 엔드포인트 매핑 (실제 V1 API 엔드포인트)
                endpoint_map = {
                    "news": f"/collect_news/{ticker}",
                    "twitter": f"/search_tweets/{ticker}",
                    "sec": f"/get_filings/{ticker}"
                }
                
                endpoint = self.v1_endpoint + endpoint_map.get(self.agent_type, "")
                
                print(f"🔄 V1 API 호출: POST {endpoint}")
                
                # POST 메서드로 호출
                response = await client.post(endpoint)
                
                print(f"📡 V1 응답 상태: {response.status_code}")
                
                if response.status_code == 200:
                    v1_data = response.json()
                    print(f"✅ V1 데이터 수신: {type(v1_data)}")
                    
                    # V2 형식으로 변환
                    result = self._convert_to_v2_format(v1_data)
                    
                    print(f"📊 변환된 데이터: {result.get('count', 0)}개 항목")
                    
                    # 데이터 수집 완료 이벤트 브로드캐스트
                    await self.broadcast_event(
                        event_type="data_collected",
                        event_data={
                            "source": self.agent_type,
                            "ticker": ticker,
                            "count": len(result.get("data", []))
                        }
                    )
                    
                    await self.reply_to_message(message, result=result, success=True)
                else:
                    error_msg = f"V1 에이전트 오류: {response.status_code}"
                    error_detail = response.text[:200] if response.text else "No details"
                    print(f"❌ {error_msg} - {error_detail}")
                    await self.reply_to_message(
                        message,
                        result={"error": error_msg, "detail": error_detail},
                        success=False
                    )
                    
        except httpx.ConnectError as e:
            error_msg = f"V1 {self.agent_type} 에이전트에 연결할 수 없습니다 (port {self.v1_port})"
            print(f"❌ {error_msg}: {e}")
            await self.reply_to_message(
                message,
                result={"error": error_msg, "detail": "에이전트가 실행 중인지 확인하세요"},
                success=False
            )
        except httpx.TimeoutException as e:
            error_msg = f"V1 {self.agent_type} 에이전트 요청 시간 초과"
            print(f"❌ {error_msg}: {e}")
            await self.reply_to_message(
                message,
                result={"error": error_msg},
                success=False
            )
        except Exception as e:
            print(f"❌ 데이터 수집 오류: {type(e).__name__}: {e}")
            await self.reply_to_message(
                message,
                result={"error": str(e)},
                success=False
            )
            
    def _convert_to_v2_format(self, v1_data: Any) -> Dict:
        """V1 데이터를 V2 형식으로 변환"""
        # 기본 구조
        result = {
            "data": [],
            "source": self.agent_type,
            "count": 0
        }
        
        # V1 데이터가 리스트 형태인 경우 (대부분의 V1 에이전트는 리스트를 반환)
        if isinstance(v1_data, list):
            print(f"📋 V1 데이터: 리스트 형태 ({len(v1_data)}개 항목)")
            items = v1_data
        else:
            # 딕셔너리인 경우 키를 확인
            print(f"📋 V1 데이터: 딕셔너리 형태 (키: {list(v1_data.keys()) if isinstance(v1_data, dict) else 'N/A'})")
            items = v1_data.get("articles", v1_data.get("tweets", v1_data.get("filings", []))) if isinstance(v1_data, dict) else []
        
        # 데이터 타입별 변환
        if self.agent_type == "news":
            for item in items:
                # V1 news agent는 간단한 형태로 반환
                if isinstance(item, dict):
                    text = item.get("text", "")
                    if text:  # text 필드가 있는 경우
                        result["data"].append({
                            "title": text[:100] + "..." if len(text) > 100 else text,
                            "content": text,
                            "url": item.get("url", ""),
                            "published_at": item.get("published_at", ""),
                            "sentiment": item.get("sentiment"),
                            "source": "news",
                            "log_message": item.get("log_message", f"📰 뉴스: {text[:50]}...")
                        })
                    else:  # 일반적인 뉴스 형식
                        result["data"].append({
                            "title": item.get("title", ""),
                            "content": item.get("content", item.get("summary", "")),
                            "url": item.get("url", ""),
                            "published_at": item.get("published_at", item.get("datetime", "")),
                            "sentiment": item.get("sentiment"),
                            "source": "news",
                            "log_message": f"📰 뉴스: {item.get('title', '')[:50]}..."
                        })
                
        elif self.agent_type == "twitter":
            for item in items:
                if isinstance(item, dict):
                    text = item.get("text", "")
                    if text:  # V1 형식
                        result["data"].append({
                            "text": text,
                            "author": item.get("author", "Unknown"),
                            "created_at": item.get("created_at", ""),
                            "sentiment": item.get("sentiment"),
                            "source": "twitter",
                            "log_message": item.get("log_message", f"🐦 트윗: {text[:50]}...")
                        })
                    else:  # 일반 트윗 형식
                        result["data"].append({
                            "text": item.get("content", ""),
                            "author": item.get("user", {}).get("name", "Unknown"),
                            "created_at": item.get("created_at", ""),
                            "sentiment": item.get("sentiment"),
                            "source": "twitter",
                            "log_message": f"🐦 트윗: {item.get('content', '')[:50]}..."
                        })
                
        elif self.agent_type == "sec":
            for item in items:
                if isinstance(item, dict):
                    text = item.get("text", "")
                    if text:  # V1 형식
                        result["data"].append({
                            "form_type": "Filing",
                            "title": text[:100] + "..." if len(text) > 100 else text,
                            "filing_date": item.get("filing_date", ""),
                            "url": item.get("url", ""),
                            "sentiment": item.get("sentiment"),
                            "source": "sec",
                            "log_message": item.get("log_message", f"📄 공시: {text[:50]}...")
                        })
                    else:  # 일반 SEC 형식
                        result["data"].append({
                            "form_type": item.get("form_type", ""),
                            "title": item.get("title", item.get("form", "")),
                            "filing_date": item.get("filing_date", item.get("date", "")),
                            "url": item.get("url", ""),
                            "sentiment": item.get("sentiment"),
                            "source": "sec",
                            "log_message": f"📄 공시: {item.get('form_type', '')} - {item.get('title', '')[:30]}..."
                        })
                
        result["count"] = len(result["data"])
        print(f"✅ V2 형식 변환 완료: {result['count']}개 항목")
        return result


# 각 데이터 타입별 어댑터 인스턴스 생성
def create_news_adapter():
    return DataAgentV2Adapter(
        agent_type="news",
        v1_port=8007,
        v2_port=8207,
        name="News Agent V2",
        description="뉴스 데이터를 수집하는 V2 에이전트"
    )

def create_twitter_adapter():
    return DataAgentV2Adapter(
        agent_type="twitter",
        v1_port=8009,
        v2_port=8209,
        name="Twitter Agent V2",
        description="트위터 데이터를 수집하는 V2 에이전트"
    )

def create_sec_adapter():
    return DataAgentV2Adapter(
        agent_type="sec",
        v1_port=8010,
        v2_port=8210,
        name="SEC Agent V2",
        description="SEC 공시 데이터를 수집하는 V2 에이전트"
    )


# FastAPI 앱 생성 함수들
def create_news_app():
    agent = create_news_adapter()
    app = agent.app
    
    @app.on_event("startup")
    async def startup():
        await agent.start()
        
    @app.on_event("shutdown")
    async def shutdown():
        await agent.stop()
        
    return app

def create_twitter_app():
    agent = create_twitter_adapter()
    app = agent.app
    
    @app.on_event("startup")
    async def startup():
        await agent.start()
        
    @app.on_event("shutdown")
    async def shutdown():
        await agent.stop()
        
    return app

def create_sec_app():
    agent = create_sec_adapter()
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
        print("Usage: python data_agent_v2_adapter.py [news|twitter|sec]")
        sys.exit(1)
        
    agent_type = sys.argv[1]
    
    if agent_type == "news":
        agent = create_news_adapter()
    elif agent_type == "twitter":
        agent = create_twitter_adapter()
    elif agent_type == "sec":
        agent = create_sec_adapter()
    else:
        print(f"Unknown agent type: {agent_type}")
        sys.exit(1)
        
    agent.run()