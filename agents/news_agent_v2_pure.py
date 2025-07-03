#!/usr/bin/env python3
"""News Agent V2 - A2A 프로토콜 기반 뉴스 데이터 수집 에이전트"""

import os
import json
import httpx
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
# from googletrans import Translator  # 임시로 비활성화
from a2a_core.base.base_agent import BaseAgent
from a2a_core.protocols.message import A2AMessage, MessageType
from pydantic import BaseModel

class NewsRequest(BaseModel):
    ticker: str

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsAgentV2(BaseAgent):
    """뉴스 데이터 수집 A2A 에이전트"""
    
    def __init__(self):
        super().__init__(
            name="News Agent V2 Pure",
            description="뉴스 데이터를 수집하는 순수 V2 A2A 에이전트",
            port=8207
        )
        
        # API 키 설정
        self.finnhub_api_key = os.getenv("FINNHUB_API_KEY")
        self.news_api_key = os.getenv("NEWS_API_KEY")
        
        # 번역기 초기화 (임시로 비활성화)
        # self.translator = Translator()
        
        # 회사명 - 티커 매핑
        self.ticker_to_company = {
            "AAPL": "Apple",
            "GOOGL": "Google", 
            "MSFT": "Microsoft",
            "AMZN": "Amazon",
            "META": "Meta",
            "TSLA": "Tesla",
            "NVDA": "NVIDIA"
        }
        
        # 금융 용어 사전 (영어 -> 한국어)
        self.finance_terms = {
            "revenue": "매출",
            "earnings": "수익",
            "profit": "이익",
            "loss": "손실",
            "growth": "성장",
            "decline": "하락",
            "surge": "급등",
            "plunge": "급락",
            "rally": "상승",
            "bear market": "약세장",
            "bull market": "강세장",
            "volatility": "변동성",
            "dividend": "배당금",
            "acquisition": "인수",
            "merger": "합병",
            "IPO": "기업공개",
            "stake": "지분",
            "shares": "주식",
            "stock": "주식",
            "market cap": "시가총액",
            "valuation": "가치평가",
            "forecast": "전망",
            "guidance": "가이던스",
            "outlook": "전망",
            "beat": "상회",
            "miss": "하회",
            "estimate": "예상치",
            "consensus": "컨센서스",
            "upgrade": "상향",
            "downgrade": "하향",
            "target price": "목표주가",
            "buy": "매수",
            "sell": "매도",
            "hold": "보유",
            "outperform": "시장수익률 상회",
            "underperform": "시장수익률 하회"
        }
        
        # HTTP 엔드포인트 추가
        self._setup_http_endpoints()
        
    def _setup_http_endpoints(self):
        """HTTP 엔드포인트 설정"""
        @self.app.post("/collect_news_data")
        async def collect_news_data(request: NewsRequest):
            """HTTP 엔드포인트로 뉴스 데이터 수집"""
            ticker = request.ticker
            logger.info(f"📰 HTTP 요청으로 뉴스 수집: {ticker}")
            
            # 뉴스 데이터 수집
            news_data = await self._collect_news_data(ticker)
            
            return {
                "data": news_data,
                "count": len(news_data),
                "source": "news",
                "log_message": f"✅ {ticker} 뉴스 {len(news_data)}개 수집 완료"
            }
        
    async def on_start(self):
        """에이전트 시작 시 호출"""
        # 능력 등록
        await self.register_capability({
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
        })
        
    async def on_stop(self):
        """에이전트 종료 시 호출"""
        pass
        
    async def handle_message(self, message: A2AMessage):
        """메시지 처리"""
        logger.info(f"🔍 메시지 수신 - Type: {message.header.message_type}, Action: {message.body.get('action')}")
        
        if message.header.message_type == MessageType.REQUEST:
            action = message.body.get("action")
            
            if action == "news_data_collection":
                await self._handle_news_collection(message)
            else:
                await self.reply_to_message(
                    message, 
                    {"error": f"Unknown action: {action}"}, 
                    success=False
                )
                
    async def _handle_news_collection(self, message: A2AMessage):
        """뉴스 수집 요청 처리"""
        try:
            payload = message.body.get("payload", {})
            ticker = payload.get("ticker")
            
            if not ticker:
                await self.reply_to_message(
                    message,
                    {"error": "Ticker is required"},
                    success=False
                )
                return
                
            logger.info(f"📰 뉴스 수집 시작: {ticker}")
            
            # 뉴스 데이터 수집
            news_data = await self._collect_news_data(ticker)
            
            # 데이터 수집 완료 이벤트 브로드캐스트
            await self.broadcast_event(
                event_type="data_collected",
                event_data={
                    "source": "news",
                    "ticker": ticker,
                    "count": len(news_data),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # 응답 전송
            result = {
                "data": news_data,
                "source": "news",
                "count": len(news_data)
            }
            
            logger.info(f"✅ 뉴스 수집 완료: {len(news_data)}개 항목")
            await self.reply_to_message(message, result, success=True)
            
        except Exception as e:
            logger.error(f"❌ 뉴스 수집 중 오류: {e}")
            await self.reply_to_message(
                message,
                {"error": str(e)},
                success=False
            )
            
    async def _collect_news_data(self, ticker: str) -> List[Dict]:
        """실제 뉴스 데이터 수집"""
        company_name = self.ticker_to_company.get(ticker.upper(), ticker)
        all_news = []
        
        # Finnhub API를 사용한 뉴스 수집
        if self.finnhub_api_key:
            finnhub_news = await self._collect_finnhub_news(ticker)
            all_news.extend(finnhub_news)
            
        # NewsAPI 사용 (NEWS_API_KEY가 있는 경우)
        if self.news_api_key and len(all_news) < 5:
            newsapi_news = await self._collect_newsapi_news(ticker, company_name)
            all_news.extend(newsapi_news)
            
        # 중복 제거 및 정렬
        unique_news = self._remove_duplicates(all_news)
        sorted_news = sorted(unique_news, key=lambda x: x.get("published_date", ""), reverse=True)
        
        return sorted_news[:10]  # 최대 10개
        
    async def _collect_finnhub_news(self, ticker: str) -> List[Dict]:
        """Finnhub API를 사용한 뉴스 수집"""
        news_items = []
        
        try:
            async with httpx.AsyncClient() as client:
                to_date = datetime.now()
                from_date = to_date - timedelta(days=7)
                
                response = await client.get(
                    "https://finnhub.io/api/v1/company-news",
                    params={
                        "symbol": ticker,
                        "from": from_date.strftime("%Y-%m-%d"),
                        "to": to_date.strftime("%Y-%m-%d"),
                        "token": self.finnhub_api_key
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for item in data[:5]:
                        # 원본 제목과 내용
                        original_title = item.get("headline", "")
                        original_content = item.get("summary", "")
                        
                        # 번역
                        translated_title = await self._translate_text(original_title)
                        translated_content = await self._translate_text(original_content)
                        
                        news_items.append({
                            "title": original_title,
                            "title_kr": translated_title,
                            "content": original_content,
                            "content_kr": translated_content,
                            "url": item.get("url", ""),
                            "source": item.get("source", "Finnhub"),
                            "published_date": datetime.fromtimestamp(item.get("datetime", 0)).isoformat(),
                            "sentiment": "neutral"
                        })
                        
        except Exception as e:
            logger.error(f"Finnhub API 오류: {e}")
            
        return news_items
        
    async def _collect_newsapi_news(self, ticker: str, company_name: str) -> List[Dict]:
        """NewsAPI를 사용한 뉴스 수집"""
        news_items = []
        
        try:
            async with httpx.AsyncClient() as client:
                # NewsAPI는 주식 티커보다 회사명으로 검색하는 것이 효과적
                query = f"{company_name} OR {ticker}"
                
                response = await client.get(
                    "https://newsapi.org/v2/everything",
                    params={
                        "q": query,
                        "apiKey": self.news_api_key,
                        "language": "en",
                        "sortBy": "relevancy",
                        "pageSize": 10
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    articles = data.get("articles", [])
                    
                    for article in articles[:5]:
                        # 원본 제목과 내용
                        original_title = article.get("title", "")
                        original_content = article.get("description", "") or article.get("content", "")
                        
                        # 번역
                        translated_title = await self._translate_text(original_title)
                        translated_content = await self._translate_text(original_content)
                        
                        news_items.append({
                            "title": original_title,
                            "title_kr": translated_title,
                            "content": original_content,
                            "content_kr": translated_content,
                            "url": article.get("url", ""),
                            "source": article.get("source", {}).get("name", "NewsAPI"),
                            "published_date": article.get("publishedAt", ""),
                            "sentiment": "neutral"
                        })
                else:
                    logger.error(f"NewsAPI 오류: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"NewsAPI 호출 오류: {e}")
            
        return news_items
        
    def _generate_mock_news(self, ticker: str, company_name: str) -> List[Dict]:
        """모의 뉴스 데이터 생성 - 티커별로 다른 내용"""
        now = datetime.now()
        
        # 티커별 특화된 뉴스
        ticker_specific_news = {
            "AAPL": [
                {
                    "title": "애플, 차세대 M4 칩 맥북 프로 출시 임박",
                    "content": "애플이 차세대 M4 칩을 탑재한 맥북 프로를 곧 출시할 예정입니다. 성능이 기존 대비 40% 향상되어 크리에이터들의 관심을 끌고 있습니다.",
                    "sentiment": "positive",
                    "source": "Bloomberg"
                },
                {
                    "title": "애플, 중국 시장에서 화웨이에 밀려 점유율 하락",
                    "content": "애플이 중국 스마트폰 시장에서 화웨이의 공세에 밀려 점유율이 하락했습니다. 현지화 전략 부재가 원인으로 지적됩니다.",
                    "sentiment": "negative",
                    "source": "Financial Times"
                },
                {
                    "title": "애플 서비스 부문 매출 200억 달러 돌파 전망",
                    "content": "애플의 서비스 부문 매출이 올해 200억 달러를 돌파할 전망입니다. 애플 뮤직, TV+ 구독자 증가가 주요 동력입니다.",
                    "sentiment": "positive",
                    "source": "Reuters"
                },
                {
                    "title": "EU, 애플에 앱스토어 독점 관련 추가 규제 검토",
                    "content": "EU가 애플의 앱스토어 정책에 대해 추가 규제를 검토하고 있습니다. 수수료 정책 변경 압박이 거세질 전망입니다.",
                    "sentiment": "negative",
                    "source": "Wall Street Journal"
                },
                {
                    "title": "애플, 인도 생산 비중 25%로 확대 계획",
                    "content": "애플이 인도 생산 비중을 현재 7%에서 25%까지 확대할 계획입니다. 중국 의존도를 낮추기 위한 전략으로 풀이됩니다.",
                    "sentiment": "neutral",
                    "source": "CNBC"
                }
            ],
            "TSLA": [
                {
                    "title": "테슬라, 사이버트럭 주간 생산 1000대 돌파",
                    "content": "테슬라가 사이버트럭 주간 생산량 1000대를 돌파했습니다. 초기 생산 목표를 달성하며 수익성 개선이 기대됩니다.",
                    "sentiment": "positive",
                    "source": "Reuters"
                },
                {
                    "title": "테슬라 FSD, 안전성 문제로 NHTSA 조사 착수",
                    "content": "미국 도로교통안전청(NHTSA)이 테슬라 FSD의 안전성 문제로 조사에 착수했습니다. 여러 건의 사고가 보고된 것으로 알려졌습니다.",
                    "sentiment": "negative",
                    "source": "Bloomberg"
                },
                {
                    "title": "테슬라, 멕시코 기가팩토리 건설 재개",
                    "content": "테슬라가 멕시코 기가팩토리 건설을 재개했습니다. 2025년 가동을 목표로 하며 연간 100만대 생산 능력을 갖출 예정입니다.",
                    "sentiment": "positive",
                    "source": "Financial Times"
                },
                {
                    "title": "테슬라 에너지 사업부, 분기 매출 15억 달러 달성",
                    "content": "테슬라 에너지 사업부가 분기 매출 15억 달러를 달성했습니다. 메가팩 수요 증가가 주요 성장 동력으로 작용했습니다.",
                    "sentiment": "positive",
                    "source": "Wall Street Journal"
                },
                {
                    "title": "테슬라, 유럽 전기차 시장 점유율 소폭 하락",
                    "content": "테슬라의 유럽 전기차 시장 점유율이 소폭 하락했습니다. 현지 브랜드들의 경쟁력 강화가 원인으로 분석됩니다.",
                    "sentiment": "neutral",
                    "source": "CNBC"
                }
            ],
            "NVDA": [
                {
                    "title": "엔비디아, 차세대 AI 칩 'Blackwell' 대량 생산 시작",
                    "content": "엔비디아가 차세대 AI 칩 'Blackwell'의 대량 생산을 시작했습니다. 성능이 기존 대비 2.5배 향상되어 수요가 폭발적일 것으로 예상됩니다.",
                    "sentiment": "positive",
                    "source": "Bloomberg"
                },
                {
                    "title": "미국, 엔비디아 중국 수출 추가 제재 검토",
                    "content": "미국 정부가 엔비디아의 중국 수출에 대해 추가 제재를 검토하고 있습니다. AI 칩 기술 유출 우려가 제기되고 있습니다.",
                    "sentiment": "negative",
                    "source": "Financial Times"
                },
                {
                    "title": "엔비디아, 주요 클라우드 업체와 5년 공급 계약 체결",
                    "content": "엔비디아가 주요 클라우드 서비스 업체들과 5년간 AI 칩 공급 계약을 체결했습니다. 계약 규모는 500억 달러에 달합니다.",
                    "sentiment": "positive",
                    "source": "Reuters"
                },
                {
                    "title": "엔비디아 CEO, 'AI 거품론' 일축",
                    "content": "젠슨 황 엔비디아 CEO가 AI 거품론을 일축했습니다. AI 혁명은 이제 시작 단계라며 장기 성장을 확신한다고 밝혔습니다.",
                    "sentiment": "positive",
                    "source": "Wall Street Journal"
                },
                {
                    "title": "경쟁사들, 엔비디아 CUDA 독점에 대항 연합 결성",
                    "content": "AMD, 인텔 등이 엔비디아의 CUDA 독점에 대항하는 개방형 표준 연합을 결성했습니다. 시장 경쟁 구도에 변화가 예상됩니다.",
                    "sentiment": "neutral",
                    "source": "CNBC"
                }
            ]
        }
        
        # 기본 뉴스 템플릿
        default_news = [
            {
                "title": f"{company_name} 주가 변동성 확대",
                "content": f"{company_name}의 주가가 최근 변동성이 확대되고 있습니다. 시장 참가자들의 관망세가 이어지고 있습니다.",
                "sentiment": "neutral",
                "source": "Reuters"
            },
            {
                "title": f"{company_name}, 신규 사업 진출 검토",
                "content": f"{company_name}이 신규 사업 진출을 검토하고 있는 것으로 알려졌습니다. 구체적인 계획은 아직 공개되지 않았습니다.",
                "sentiment": "neutral",
                "source": "Bloomberg"
            }
        ]
        
        # 티커에 맞는 뉴스 선택
        news_templates = ticker_specific_news.get(ticker, default_news)
        
        news_items = []
        for i, template in enumerate(news_templates[:5]):  # 최대 5개
            news_items.append({
                "title": template["title"],
                "title_kr": template["title"],  # 모의 데이터는 이미 한글
                "content": template["content"],
                "content_kr": template["content"],  # 모의 데이터는 이미 한글
                "url": f"https://example.com/news/{ticker}-{i}",
                "source": template["source"],
                "published_date": (now - timedelta(hours=i*6)).isoformat(),
                "sentiment": template.get("sentiment", "neutral")
            })
            
        return news_items
        
    def _remove_duplicates(self, news_list: List[Dict]) -> List[Dict]:
        """중복 뉴스 제거"""
        seen_titles = set()
        unique_news = []
        
        for item in news_list:
            title = item.get("title", "").lower().strip()
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_news.append(item)
                
        return unique_news
    
    async def _translate_text(self, text: str) -> str:
        """텍스트를 한국어로 번역"""
        if not text:
            return ""
            
        try:
            # 먼저 금융 용어 사전으로 치환
            translated = text
            for eng_term, kor_term in self.finance_terms.items():
                # 대소문자 구분 없이 치환
                import re
                pattern = re.compile(re.escape(eng_term), re.IGNORECASE)
                translated = pattern.sub(kor_term, translated)
            
            # Google Translate API로 전체 번역 (임시로 키워드 기반 번역만 사용)
            # result = self.translator.translate(translated, src='en', dest='ko')
            # return result.text
            
            # 키워드 기반 번역만 반환
            # 금융 용어가 하나라도 치환되었는지 확인
            if translated != text:
                return translated
            else:
                return text[:100] + "..."  # 원문 일부 반환
            
        except Exception as e:
            logger.warning(f"번역 오류: {e}")
            # 번역 실패 시 원본 반환
            return text

# 에이전트 인스턴스 생성
agent = NewsAgentV2()

# BaseAgent의 app을 사용
app = agent.app

# 앱 시작 시 에이전트 시작
@app.on_event("startup")
async def startup():
    print("🚀 News Agent V2 Pure 시작 중...")
    await agent.start()

# 앱 종료 시 에이전트 정리
@app.on_event("shutdown")
async def shutdown():
    await agent.stop()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8207)