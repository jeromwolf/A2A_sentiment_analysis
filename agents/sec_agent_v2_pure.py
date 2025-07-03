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
                return []  # 빈 데이터 반환
                
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
                        
                        # 폼 타입별 설명 추가
                        form_descriptions = {
                            "10-K": "연간 보고서 - 회사의 연간 실적 및 재무상태",
                            "10-Q": "분기 보고서 - 분기별 실적 및 경영 현황",
                            "8-K": "임시 보고서 - 주요 이벤트 및 경영상 중요 변경사항",
                            "4": "내부자 거래 - 임원진의 주식 매매 내역",
                            "DEF 14A": "주주총회 위임장 - 주주총회 안건 및 임원 보수",
                            "144": "제한 주식 매도 신고 - 내부자의 주식 매도 계획",
                            "S-8": "직원 주식 옵션 - 직원 대상 주식 발행 계획",
                            "S-3": "유가증권 신고서 - 신규 증권 발행 계획"
                        }
                        
                        form_desc = form_descriptions.get(forms[i], "기타 공시")
                        
                        # SEC 공시 제목과 요약 생성
                        title = f"{ticker} {forms[i]} 공시 ({dates[i]})"
                        content = f"{form_desc}. 이 공시는 {ticker}의 {forms[i]} 양식으로 제출된 공식 문서입니다."
                        
                        formatted_filings.append({
                            "form_type": forms[i],
                            "title": title,
                            "content": content,
                            "description": form_desc,
                            "filing_date": dates[i],
                            "url": filing_url,
                            "source": "sec",
                            "sentiment": None,  # 나중에 감정분석에서 채움
                            "log_message": f"📄 공시: {forms[i]} - {dates[i]}"
                        })
                        
                    return formatted_filings
                else:
                    print(f"❌ SEC API 오류: {response.status_code}")
                    return []  # 빈 데이터 반환
                    
        except Exception as e:
            print(f"❌ SEC API 호출 오류: {e}")
            return []  # 빈 데이터 반환
            
    def _get_mock_filings(self, ticker: str) -> List[Dict]:
        """모의 공시 데이터 생성 - 티커별로 다른 내용"""
        today = datetime.now()
        
        # 티커별 특화된 공시 데이터
        ticker_specific_filings = {
            "AAPL": [
                {
                    "form_type": "10-K",
                    "title": "Annual Report - 2024 회계연도 매출 4,000억 달러 돌파",
                    "filing_date": (today - timedelta(days=30)).strftime("%Y-%m-%d"),
                    "url": f"https://sec.gov/example/{ticker}/10K-2024",
                    "source": "sec",
                    "sentiment": None,
                    "content": "애플 연간 매출 사상 최대 기록. 서비스 부문 성장이 견인",
                    "log_message": "📄 공시: 10-K - 연간 매출 최대 기록"
                },
                {
                    "form_type": "10-Q",
                    "title": "Quarterly Report - Q3 2024 아이폰 판매 둔화",
                    "filing_date": (today - timedelta(days=10)).strftime("%Y-%m-%d"),
                    "url": f"https://sec.gov/example/{ticker}/10Q-Q3-2024",
                    "source": "sec",
                    "sentiment": None,
                    "content": "3분기 아이폰 판매량 전년 대비 5% 감소. 중국 시장 부진",
                    "log_message": "📄 공시: 10-Q - 아이폰 판매 둔화"
                },
                {
                    "form_type": "8-K",
                    "title": "Current Report - 자사주 900억 달러 매입 발표",
                    "filing_date": (today - timedelta(days=2)).strftime("%Y-%m-%d"),
                    "url": f"https://sec.gov/example/{ticker}/8K-buyback",
                    "source": "sec",
                    "sentiment": None,
                    "content": "애플 이사회, 900억 달러 규모 자사주 매입 프로그램 승인",
                    "log_message": "📄 공시: 8-K - 대규모 자사주 매입"
                },
                {
                    "form_type": "8-K",
                    "title": "Current Report - AI 연구개발 투자 확대",
                    "filing_date": (today - timedelta(days=5)).strftime("%Y-%m-%d"),
                    "url": f"https://sec.gov/example/{ticker}/8K-ai",
                    "source": "sec",
                    "sentiment": None,
                    "content": "AI 및 머신러닝 연구개발에 50억 달러 추가 투자 계획",
                    "log_message": "📄 공시: 8-K - AI R&D 투자"
                },
                {
                    "form_type": "DEF 14A",
                    "title": "Proxy Statement - 임원 보수 15% 인상",
                    "filing_date": (today - timedelta(days=15)).strftime("%Y-%m-%d"),
                    "url": f"https://sec.gov/example/{ticker}/DEF14A",
                    "source": "sec",
                    "sentiment": None,
                    "content": "주주총회 안건: CEO 및 주요 임원 보수 인상안",
                    "log_message": "📄 공시: DEF 14A - 임원 보수"
                }
            ],
            "TSLA": [
                {
                    "form_type": "10-K",
                    "title": "Annual Report - 2024 차량 인도량 180만대 달성",
                    "filing_date": (today - timedelta(days=30)).strftime("%Y-%m-%d"),
                    "url": f"https://sec.gov/example/{ticker}/10K-2024",
                    "source": "sec",
                    "sentiment": None,
                    "content": "테슬라 연간 차량 인도량 180만대로 전년 대비 35% 성장",
                    "log_message": "📄 공시: 10-K - 차량 인도량 신기록"
                },
                {
                    "form_type": "10-Q",
                    "title": "Quarterly Report - Q3 2024 영업이익률 9.6%",
                    "filing_date": (today - timedelta(days=10)).strftime("%Y-%m-%d"),
                    "url": f"https://sec.gov/example/{ticker}/10Q-Q3-2024",
                    "source": "sec",
                    "sentiment": None,
                    "content": "3분기 영업이익률 개선. 제조 효율성 향상 효과",
                    "log_message": "📄 공시: 10-Q - 수익성 개선"
                },
                {
                    "form_type": "8-K",
                    "title": "Current Report - 멕시코 기가팩토리 건설 착수",
                    "filing_date": (today - timedelta(days=2)).strftime("%Y-%m-%d"),
                    "url": f"https://sec.gov/example/{ticker}/8K-mexico",
                    "source": "sec",
                    "sentiment": None,
                    "content": "멕시코 기가팩토리 건설 공식 착수. 100억 달러 투자",
                    "log_message": "📄 공시: 8-K - 멕시코 공장"
                },
                {
                    "form_type": "8-K",
                    "title": "Current Report - FSD v12 베타 출시",
                    "filing_date": (today - timedelta(days=7)).strftime("%Y-%m-%d"),
                    "url": f"https://sec.gov/example/{ticker}/8K-fsd",
                    "source": "sec",
                    "sentiment": None,
                    "content": "완전자율주행(FSD) v12 베타 버전 북미 시장 출시",
                    "log_message": "📄 공시: 8-K - FSD 업데이트"
                },
                {
                    "form_type": "8-K",
                    "title": "Current Report - 에너지 사업부 분사 검토",
                    "filing_date": (today - timedelta(days=20)).strftime("%Y-%m-%d"),
                    "url": f"https://sec.gov/example/{ticker}/8K-energy",
                    "source": "sec",
                    "sentiment": None,
                    "content": "에너지 저장장치 사업부 분사 가능성 검토 중",
                    "log_message": "📄 공시: 8-K - 사업부 분사"
                }
            ],
            "NVDA": [
                {
                    "form_type": "10-K",
                    "title": "Annual Report - 2024 데이터센터 매출 600% 성장",
                    "filing_date": (today - timedelta(days=30)).strftime("%Y-%m-%d"),
                    "url": f"https://sec.gov/example/{ticker}/10K-2024",
                    "source": "sec",
                    "sentiment": None,
                    "content": "AI 붐으로 데이터센터 부문 매출 전년 대비 600% 급증",
                    "log_message": "📄 공시: 10-K - 데이터센터 매출 급증"
                },
                {
                    "form_type": "10-Q",
                    "title": "Quarterly Report - Q3 2024 매출 181억 달러",
                    "filing_date": (today - timedelta(days=10)).strftime("%Y-%m-%d"),
                    "url": f"https://sec.gov/example/{ticker}/10Q-Q3-2024",
                    "source": "sec",
                    "sentiment": None,
                    "content": "3분기 매출 시장 예상치 20% 상회. H100 수요 지속",
                    "log_message": "📄 공시: 10-Q - 실적 서프라이즈"
                },
                {
                    "form_type": "8-K",
                    "title": "Current Report - H200 칩 대량 생산 시작",
                    "filing_date": (today - timedelta(days=2)).strftime("%Y-%m-%d"),
                    "url": f"https://sec.gov/example/{ticker}/8K-h200",
                    "source": "sec",
                    "sentiment": None,
                    "content": "차세대 AI 칩 H200 대량 생산 돌입. 성능 70% 향상",
                    "log_message": "📄 공시: 8-K - H200 생산"
                },
                {
                    "form_type": "8-K",
                    "title": "Current Report - 중국 수출 제한 대응 계획",
                    "filing_date": (today - timedelta(days=8)).strftime("%Y-%m-%d"),
                    "url": f"https://sec.gov/example/{ticker}/8K-china",
                    "source": "sec",
                    "sentiment": None,
                    "content": "중국 시장용 규제 준수 칩 개발. 성능 제한 버전 출시",
                    "log_message": "📄 공시: 8-K - 중국 대응"
                },
                {
                    "form_type": "8-K",
                    "title": "Current Report - ARM 인수 철회 후 파트너십",
                    "filing_date": (today - timedelta(days=25)).strftime("%Y-%m-%d"),
                    "url": f"https://sec.gov/example/{ticker}/8K-arm",
                    "source": "sec",
                    "sentiment": None,
                    "content": "ARM과 20년 라이선스 계약 체결. CPU 설계 협력 강화",
                    "log_message": "📄 공시: 8-K - ARM 파트너십"
                }
            ]
        }
        
        # 기본 공시 템플릿
        default_filings = [
            {
                "form_type": "10-K",
                "title": "Annual Report",
                "filing_date": (today - timedelta(days=30)).strftime("%Y-%m-%d"),
                "url": f"https://sec.gov/example/{ticker}/10K",
                "source": "sec",
                "sentiment": None,
                "content": "연간 보고서",
                "log_message": "📄 공시: 10-K - Annual Report"
            },
            {
                "form_type": "10-Q",
                "title": "Quarterly Report",
                "filing_date": (today - timedelta(days=10)).strftime("%Y-%m-%d"),
                "url": f"https://sec.gov/example/{ticker}/10Q",
                "source": "sec",
                "sentiment": None,
                "content": "분기 보고서",
                "log_message": "📄 공시: 10-Q - Quarterly Report"
            },
            {
                "form_type": "8-K",
                "title": "Current Report",
                "filing_date": (today - timedelta(days=2)).strftime("%Y-%m-%d"),
                "url": f"https://sec.gov/example/{ticker}/8K",
                "source": "sec",
                "sentiment": None,
                "content": "임시 보고서",
                "log_message": "📄 공시: 8-K - Current Report"
            }
        ]
        
        # 티커에 맞는 공시 선택
        filings_template = ticker_specific_filings.get(ticker, default_filings)
        
        return filings_template[:self.max_filings]


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