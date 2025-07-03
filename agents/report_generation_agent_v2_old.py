"""
보고서 생성 에이전트 V2 - A2A 프로토콜 기반
최종 점수와 분석 결과를 받아 전문적인 투자 보고서 생성
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI
from contextlib import asynccontextmanager

from a2a_core.base.base_agent import BaseAgent
from a2a_core.protocols.message import A2AMessage, MessageType

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReportGenerationAgentV2(BaseAgent):
    """보고서 생성 A2A 에이전트"""
    
    def __init__(self):
        super().__init__(
            name="Report Generation Agent V2",
            description="투자 분석 결과를 기반으로 전문적인 보고서를 생성하는 A2A 에이전트",
            port=8204
        )
        self.capabilities = [
            {
                "name": "report_generation",
                "version": "2.0",
                "description": "투자 분석 결과를 기반으로 전문적인 보고서 생성",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string", "description": "주식 티커"},
                        "company_name": {"type": "string", "description": "회사명"},
                        "final_score": {"type": "number", "description": "최종 점수"},
                        "sentiment": {"type": "string", "description": "최종 감정"},
                        "score_details": {"type": "object", "description": "점수 상세 정보"},
                        "data_summary": {"type": "object", "description": "데이터 수집 요약"},
                        "sentiment_analysis": {"type": "array", "description": "감정 분석 결과"}
                    },
                    "required": ["ticker", "final_score", "sentiment"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "report": {"type": "string"},
                        "summary": {"type": "string"},
                        "recommendation": {"type": "string"}
                    }
                }
            }
        ]
    
    async def handle_message(self, message: A2AMessage) -> Optional[A2AMessage]:
        """메시지 처리"""
        logger.info(f"🔍 메시지 수신 - Type: {message.header.message_type}, Action: {message.body.get('action')}")
        
        if message.header.message_type == MessageType.REQUEST:
            action = message.body.get("action")
            
            if action == "report_generation":
                return await self._handle_report_generation(message)
        
        return None
    
    async def _handle_report_generation(self, message: A2AMessage) -> A2AMessage:
        """보고서 생성 요청 처리"""
        try:
            payload = message.body.get("payload", {})
            ticker = payload.get("ticker", "")
            company_name = payload.get("company_name", ticker)
            final_score = payload.get("final_score", 0)
            sentiment = payload.get("sentiment", "neutral")
            score_details = payload.get("score_details", {})
            data_summary = payload.get("data_summary", {})
            sentiment_analysis = payload.get("sentiment_analysis", [])
            
            logger.info(f"📝 보고서 생성 시작 - 티커: {ticker}")
            
            # 보고서 생성
            report = self._generate_professional_report(
                ticker=ticker,
                company_name=company_name,
                final_score=final_score,
                sentiment=sentiment,
                score_details=score_details,
                data_summary=data_summary,
                sentiment_analysis=sentiment_analysis
            )
            
            # 요약 생성
            summary = self._generate_summary(ticker, company_name, final_score, sentiment)
            
            # 투자 추천 생성
            recommendation = self._generate_recommendation(final_score, sentiment)
            
            response_data = {
                "report": report,
                "summary": summary,
                "recommendation": recommendation,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"✅ 보고서 생성 완료 - 추천: {recommendation}")
            
            # 이벤트 브로드캐스트
            await self._broadcast_report_generated(ticker, recommendation)
            
            # 응답 전송
            await self.reply_to_message(
                original_message=message,
                result=response_data,
                success=True
            )
            
            return None  # reply_to_message가 직접 응답을 전송함
            
        except Exception as e:
            logger.error(f"❌ 보고서 생성 실패: {str(e)}")
            await self.reply_to_message(
                original_message=message,
                result={"error": str(e)},
                success=False
            )
            return None
    
    def _generate_professional_report(
        self, 
        ticker: str,
        company_name: str,
        final_score: float,
        sentiment: str,
        score_details: Dict,
        data_summary: Dict,
        sentiment_analysis: List[Dict]
    ) -> str:
        """전문적인 투자 보고서 생성"""
        
        # 감정 표현
        sentiment_kr = {
            "positive": "긍정적",
            "negative": "부정적",
            "neutral": "중립적"
        }.get(sentiment, "중립적")
        
        # 점수 설명
        score_description = self._get_score_description(final_score)
        
        # 소스별 통계
        source_stats = score_details.get("source_averages", {})
        source_counts = score_details.get("source_counts", {})
        
        report = f"""
====================================================================
                    {company_name} ({ticker}) 투자 분석 보고서
====================================================================

생성일시: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}

1. 종합 평가
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 투자 심리 점수: {final_score:.2f} ({sentiment_kr})
• 평가 등급: {score_description}
• 분석 기간: 최근 7일

2. 데이터 수집 현황
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        # 데이터 수집 통계 추가
        total_items = sum(source_counts.values()) if source_counts else 0
        
        if source_counts.get("sec", 0) > 0:
            report += f"• SEC 공시: {source_counts['sec']}건 (평균 점수: {source_stats.get('sec', 0):.2f})\n"
        if source_counts.get("news", 0) > 0:
            report += f"• 뉴스 기사: {source_counts['news']}건 (평균 점수: {source_stats.get('news', 0):.2f})\n"
        if source_counts.get("twitter", 0) > 0:
            report += f"• 소셜 미디어: {source_counts['twitter']}건 (평균 점수: {source_stats.get('twitter', 0):.2f})\n"
        
        report += f"• 총 분석 항목: {total_items}건\n"
        
        # 가중치 정보
        report += f"""
3. 분석 방법론
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• SEC 공시 가중치: 1.5 (가장 신뢰도 높음)
• 뉴스 기사 가중치: 1.0 (기본 가중치)
• 소셜 미디어 가중치: 0.7 (상대적으로 낮은 신뢰도)

4. 주요 분석 내용
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        # 긍정적/부정적 항목 분리
        positive_items = [item for item in sentiment_analysis if item.get("score", 0) > 0.3]
        negative_items = [item for item in sentiment_analysis if item.get("score", 0) < -0.3]
        
        if positive_items:
            report += f"\n【긍정적 요인】 ({len(positive_items)}건)\n"
            for i, item in enumerate(positive_items[:3], 1):  # 상위 3개만
                source = item.get("source", "unknown")
                content = item.get("content", "")[:100] + "..."
                score = item.get("score", 0)
                report += f"  {i}. [{source}] {content} (점수: {score:.2f})\n"
        
        if negative_items:
            report += f"\n【부정적 요인】 ({len(negative_items)}건)\n"
            for i, item in enumerate(negative_items[:3], 1):  # 상위 3개만
                source = item.get("source", "unknown")
                content = item.get("content", "")[:100] + "..."
                score = item.get("score", 0)
                report += f"  {i}. [{source}] {content} (점수: {score:.2f})\n"
        
        # 투자 권고사항
        recommendation = self._generate_recommendation(final_score, sentiment)
        
        report += f"""
5. 투자 권고사항
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{recommendation}

6. 리스크 고지
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 본 보고서는 AI 기반 감정 분석 결과이며, 투자 결정의 참고 자료로만 활용하시기 바랍니다.
• 실제 투자는 개인의 판단과 책임하에 이루어져야 합니다.
• 시장 상황은 급변할 수 있으므로 최신 정보를 지속적으로 확인하시기 바랍니다.

====================================================================
                        A2A 투자 분석 시스템 v2.0
====================================================================
"""
        
        return report
    
    def _get_score_description(self, score: float) -> str:
        """점수에 따른 등급 설명"""
        if score > 0.6:
            return "매우 긍정적 ⭐⭐⭐⭐⭐"
        elif score > 0.3:
            return "긍정적 ⭐⭐⭐⭐"
        elif score > -0.3:
            return "중립적 ⭐⭐⭐"
        elif score > -0.6:
            return "부정적 ⭐⭐"
        else:
            return "매우 부정적 ⭐"
    
    def _generate_summary(self, ticker: str, company_name: str, final_score: float, sentiment: str) -> str:
        """간단한 요약 생성"""
        sentiment_kr = {
            "positive": "긍정적",
            "negative": "부정적",
            "neutral": "중립적"
        }.get(sentiment, "중립적")
        
        return f"{company_name}({ticker})에 대한 시장 심리는 {sentiment_kr}입니다. 투자 심리 점수는 {final_score:.2f}점으로 평가되었습니다."
    
    def _generate_recommendation(self, final_score: float, sentiment: str) -> str:
        """투자 추천 생성"""
        if final_score > 0.6:
            return "강력 매수 추천 - 시장 심리가 매우 긍정적이며, 단기적으로 상승 가능성이 높습니다."
        elif final_score > 0.3:
            return "매수 추천 - 긍정적인 시장 심리를 보이고 있으며, 점진적인 상승이 예상됩니다."
        elif final_score > -0.3:
            return "관망 추천 - 중립적인 시장 심리를 보이고 있으며, 추가적인 모니터링이 필요합니다."
        elif final_score > -0.6:
            return "매도 고려 - 부정적인 시장 심리가 감지되며, 리스크 관리가 필요합니다."
        else:
            return "강력 매도 추천 - 시장 심리가 매우 부정적이며, 손실 최소화를 위한 전략이 필요합니다."
    
    async def _broadcast_report_generated(self, ticker: str, recommendation: str):
        """보고서 생성 완료 이벤트 브로드캐스트"""
        event_data = {
            "ticker": ticker,
            "recommendation": recommendation,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_event("report_generated", event_data)
        logger.info(f"📢 보고서 생성 이벤트 브로드캐스트: {ticker}")
    
    async def on_start(self):
        """에이전트 시작 시 실행"""
        logger.info("✅ Report Generation Agent V2 초기화 완료")
    
    async def on_stop(self):
        """에이전트 종료 시 실행"""
        logger.info("👋 Report Generation Agent V2 종료 중...")

# 에이전트 인스턴스 생성
agent = ReportGenerationAgentV2()

# BaseAgent의 app을 사용
app = agent.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8204)