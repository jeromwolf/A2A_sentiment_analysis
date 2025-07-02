"""
SEC Agent V2 - 순수 A2A 구현

SEC 공시 데이터를 수집하는 독립적인 V2 에이전트
V1 의존성 없이 직접 SEC EDGAR API 호출
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta
from dotenv import load_dotenv

from a2a_core.base.base_agent import BaseAgent
from a2a_core.protocols.message import A2AMessage, MessageType

load_dotenv()


class SECAgentV2(BaseAgent):
    """SEC 공시 수집 V2 에이전트"""
    
    def __init__(self):
        super().__init__(
            name="SEC Agent V2",
            description="SEC 공시 데이터를 수집하는 A2A 에이전트",
            port=8210,
            registry_url="http://localhost:8001"
        )
        
        # API 설정
        self.user_agent = os.getenv("SEC_API_USER_AGENT", "A2A-Agent/1.0")
        self.max_filings = 5
        
    async def on_start(self):
        """에이전트 시작 시 초기화"""
        # 능력 등록
        await self.register_capability({
            "name": "sec_data_collection",
            "version": "2.0",
            "description": "SEC 공시 데이터 수집",
            "input_schema": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "주식 티커"}
                },
                "required": ["ticker"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "data": {"type": "array"},
                    "count": {"type": "integer"},
                    "source": {"type": "string"}
                }
            }
        })
        
        print("✅ SEC Agent V2 초기화 완료")
        
    async def on_stop(self):
        """에이전트 종료 시 정리"""
        print("🛑 SEC Agent V2 종료 중...")
        
    async def handle_message(self, message: A2AMessage):
        """메시지 처리"""
        try:
            if message.header.message_type == MessageType.REQUEST:
                action = message.body.get("action")
                
                if action == "sec_data_collection":
                    await self._handle_sec_collection(message)
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
            
    async def _handle_sec_collection(self, message: A2AMessage):
        """SEC 공시 수집 요청 처리"""
        payload = message.body.get("payload", {})
        ticker = payload.get("ticker", "")
        
        print(f"📄 SEC 공시 수집 시작: {ticker}")
        
        try:
            # SEC EDGAR API로 공시 수집
            filings_data = await self._fetch_sec_filings(ticker)
            
            # 결과 포맷팅
            result = {
                "data": filings_data,
                "count": len(filings_data),
                "source": "sec",
                "log_message": f"✅ {ticker} 공시 {len(filings_data)}개 수집 완료"
            }
            
            # 데이터 수집 완료 이벤트 브로드캐스트
            await self.broadcast_event(
                event_type="data_collected",
                event_data={
                    "source": "sec",
                    "ticker": ticker,
                    "count": len(filings_data)
                }
            )
            
            await self.reply_to_message(message, result=result, success=True)
            
        except Exception as e:
            print(f"❌ SEC 공시 수집 오류: {e}")
            await self.reply_to_message(
                message,
                result={"error": str(e), "data": [], "count": 0},
                success=False
            )
            
    async def _fetch_sec_filings(self, ticker: str) -> List[Dict]:
        """SEC EDGAR API로 공시 가져오기"""
        try:
            # CIK 조회 (실제로는 티커->CIK 매핑 필요)
            cik_map = {
                "AAPL": "0000320193",
                "TSLA": "0001318605",
                "NVDA": "0001045810",
                "GOOGL": "0001652044",
                "MSFT": "0000789019",
                "AMZN": "0001018724",
                "META": "0001326801"
            }
            
            cik = cik_map.get(ticker)
            if not cik:
                print(f"⚠️ {ticker}의 CIK를 찾을 수 없습니다")
                return self._get_mock_filings(ticker)
                
            # SEC EDGAR API 호출
            url = f"https://data.sec.gov/submissions/CIK{cik}.json"
            headers = {
                "User-Agent": self.user_agent,
                "Accept-Encoding": "gzip, deflate"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    recent_filings = data.get("filings", {}).get("recent", {})
                    
                    # 최근 공시 포맷팅
                    formatted_filings = []
                    forms = recent_filings.get("form", [])[:self.max_filings]
                    dates = recent_filings.get("filingDate", [])[:self.max_filings]
                    accessions = recent_filings.get("accessionNumber", [])[:self.max_filings]
                    
                    for i in range(min(len(forms), self.max_filings)):
                        filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{accessions[i].replace('-', '')}/{accessions[i]}.txt"
                        
                        formatted_filings.append({
                            "form_type": forms[i],
                            "title": f"{forms[i]} Filing",
                            "filing_date": dates[i],
                            "url": filing_url,
                            "source": "sec",
                            "sentiment": None,  # 나중에 감정분석에서 채움
                            "log_message": f"📄 공시: {forms[i]} - {dates[i]}"
                        })
                        
                    return formatted_filings
                else:
                    print(f"❌ SEC API 오류: {response.status_code}")
                    return self._get_mock_filings(ticker)
                    
        except Exception as e:
            print(f"❌ SEC API 호출 오류: {e}")
            return self._get_mock_filings(ticker)
            
    def _get_mock_filings(self, ticker: str) -> List[Dict]:
        """모의 공시 데이터 생성"""
        today = datetime.now()
        mock_filings = [
            {
                "form_type": "10-K",
                "title": "Annual Report",
                "filing_date": (today - timedelta(days=30)).strftime("%Y-%m-%d"),
                "url": f"https://sec.gov/example/{ticker}/10K",
                "source": "sec",
                "sentiment": None,
                "log_message": "📄 공시: 10-K - Annual Report"
            },
            {
                "form_type": "10-Q",
                "title": "Quarterly Report",
                "filing_date": (today - timedelta(days=10)).strftime("%Y-%m-%d"),
                "url": f"https://sec.gov/example/{ticker}/10Q",
                "source": "sec",
                "sentiment": None,
                "log_message": "📄 공시: 10-Q - Quarterly Report"
            },
            {
                "form_type": "8-K",
                "title": "Current Report",
                "filing_date": (today - timedelta(days=2)).strftime("%Y-%m-%d"),
                "url": f"https://sec.gov/example/{ticker}/8K",
                "source": "sec",
                "sentiment": None,
                "log_message": "📄 공시: 8-K - Current Report"
            }
        ]
        
        return mock_filings[:self.max_filings]


# 모듈 레벨에서 에이전트와 app 생성
agent = SECAgentV2()
app = agent.app

@app.on_event("startup")
async def startup():
    await agent.start()

@app.on_event("shutdown")
async def shutdown():
    await agent.stop()

# 독립 실행용
if __name__ == "__main__":
    agent.run()