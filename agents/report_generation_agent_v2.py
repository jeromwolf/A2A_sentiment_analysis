"""
향상된 리포트 생성 에이전트 V2 - HTML 형식의 전문적인 리포트 생성
"""
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
import httpx
from datetime import datetime
import logging
from pathlib import Path
# import weasyprint  # PDF 생성은 브라우저에서 처리

from a2a_core.base.base_agent import BaseAgent
from a2a_core.protocols.message import A2AMessage, MessageType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# HTTP 요청 모델
class ReportRequest(BaseModel):
    ticker: str
    company_name: Optional[str] = None
    final_score: float
    sentiment: str
    score_details: Optional[Dict] = None
    data_summary: Optional[Dict] = None
    sentiment_analysis: Optional[List[Dict]] = None
    quantitative_data: Optional[Dict] = None
    risk_analysis: Optional[Dict] = None

class ReportGenerationAgentV2(BaseAgent):
    """리포트 생성 A2A 에이전트"""
    
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
                        "sentiment_analysis": {"type": "array", "description": "감정 분석 결과"},
                        "quantitative_data": {"type": "object", "description": "정량적 분석 데이터"},
                        "risk_analysis": {"type": "object", "description": "리스크 분석 데이터"}
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
        
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        self.GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.GEMINI_API_KEY}"
        
        # HTTP 엔드포인트 설정
        self._setup_http_endpoints()
    
    def _setup_http_endpoints(self):
        """HTTP 엔드포인트 설정"""
        @self.app.post("/generate_report")
        async def generate_report(request: ReportRequest):
            """HTTP 엔드포인트로 리포트 생성"""
            logger.info(f"📝 HTTP 요청으로 리포트 생성: {request.ticker}")
            
            # 요청 데이터를 딕셔너리로 변환
            data = request.model_dump()
            
            # 리포트 생성
            result = await self._generate_enhanced_report(data)
            
            return result
        
        # PDF 관련 엔드포인트는 브라우저에서 직접 처리하도록 변경
        # @self.app.post("/generate_report_pdf")
        # async def generate_report_pdf(request: ReportRequest):
        #     """HTTP 엔드포인트로 리포트 생성 및 PDF 저장"""
        #     pass
        
        # @self.app.post("/export_pdf")
        # async def export_pdf(request: ReportRequest):
        #     """기존 리포트를 PDF로 다운로드"""
        #     pass
    
    async def handle_message(self, message: A2AMessage):
        """메시지 처리"""
        try:
            action = message.body.get("action")
            logger.info(f"🔍 메시지 수신 - Type: {message.header.message_type}, Action: {action}")
            
            if message.header.message_type == MessageType.EVENT:
                return
            
            if message.header.message_type == MessageType.REQUEST and action == "report_generation":
                payload = message.body.get("payload", {})
                
                # 리포트 생성
                report = await self._generate_enhanced_report(payload)
                
                # 이벤트 브로드캐스트
                await self._broadcast_report_generated(
                    payload.get("ticker"),
                    report
                )
                
                # 응답 전송
                await self.reply_to_message(
                    message,
                    result=report,
                    success=True
                )
                
        except Exception as e:
            logger.error(f"❌ 리포트 생성 실패: {str(e)}")
            await self.reply_to_message(
                message,
                result={"error": str(e)},
                success=False
            )
    
    async def _generate_enhanced_report(self, data: Dict) -> Dict:
        """향상된 HTML 리포트 생성"""
        ticker = data.get("ticker", "")
        company_name = data.get("company_name") or ticker
        final_score = data.get("final_score", 0)
        sentiment = data.get("sentiment", "neutral")
        score_details = data.get("score_details", {})
        data_summary = data.get("data_summary", {})
        sentiment_analysis = data.get("sentiment_analysis", [])
        quantitative_data = data.get("quantitative_data", {})
        risk_analysis = data.get("risk_analysis", {})
        
        logger.info(f"📝 보고서 생성 시작 - 티커: {ticker}")
        logger.info(f"📊 받은 데이터 요약:")
        logger.info(f"  - sentiment_analysis 개수: {len(sentiment_analysis)}")
        logger.info(f"  - data_summary: {data_summary}")
        logger.info(f"  - score_details: {score_details}")
        logger.info(f"  - quantitative_data 존재: {'있음' if quantitative_data else '없음'}")
        logger.info(f"  - risk_analysis 존재: {'있음' if risk_analysis else '없음'}")
        if quantitative_data:
            logger.info(f"  - quantitative_data keys: {list(quantitative_data.keys())}")
        if risk_analysis:
            logger.info(f"  - risk_analysis keys: {list(risk_analysis.keys())}")
        
        # sentiment_analysis 내용 로깅
        if sentiment_analysis:
            logger.info(f"  - sentiment_analysis 샘플: {sentiment_analysis[:2]}")
        else:
            logger.warning("  ⚠️ sentiment_analysis가 비어있습니다!")
        
        # 데이터 근거 분석
        evidence_summary = self._analyze_evidence(sentiment_analysis, data_summary)
        
        # HTML 리포트 생성
        report_html = f"""
<div class="investment-report">
    <style>
        .investment-report {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: #333;
            line-height: 1.6;
        }}
        .report-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 12px 12px 0 0;
            text-align: center;
        }}
        .report-title {{
            font-size: 2em;
            margin-bottom: 10px;
        }}
        .report-subtitle {{
            opacity: 0.9;
        }}
        .score-card {{
            background: white;
            padding: 30px;
            margin: -20px 20px 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .score-value {{
            font-size: 4em;
            font-weight: bold;
            color: {self._get_score_color(final_score)};
            margin: 10px 0;
        }}
        .score-label {{
            font-size: 1.2em;
            color: #666;
        }}
        .sentiment-badge {{
            display: inline-block;
            padding: 8px 20px;
            background: {self._get_sentiment_color(sentiment)};
            color: white;
            border-radius: 20px;
            font-weight: bold;
            margin-top: 10px;
        }}
        .section {{
            background: white;
            padding: 25px;
            margin: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .section-title {{
            font-size: 1.5em;
            color: #333;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }}
        .evidence-summary {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 25px;
            border-radius: 12px;
            margin: 20px;
        }}
        .evidence-item {{
            background: white;
            padding: 20px;
            margin: 15px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .evidence-header {{
            display: flex;
            align-items: center;
            margin-bottom: 15px;
            font-weight: bold;
            color: #333;
        }}
        .evidence-icon {{
            font-size: 1.5em;
            margin-right: 10px;
        }}
        .evidence-count {{
            color: #4267B2;
            font-size: 1.2em;
        }}
        .evidence-trend {{
            margin-top: 10px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 6px;
        }}
        .conclusion-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin: 20px;
            text-align: center;
        }}
        .conclusion-title {{
            font-size: 1.8em;
            margin-bottom: 15px;
        }}
        .conclusion-text {{
            font-size: 1.2em;
            line-height: 1.6;
        }}
        .data-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .data-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}
        .data-value {{
            font-size: 1.8em;
            font-weight: bold;
            color: #4267B2;
        }}
        .data-label {{
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        .sentiment-item {{
            padding: 10px;
            margin: 8px 0;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid {self._get_score_color(final_score)};
        }}
        .risk-indicator {{
            display: flex;
            align-items: center;
            margin: 10px 0;
        }}
        .risk-label {{
            flex: 1;
            font-weight: 500;
        }}
        .risk-bar {{
            flex: 2;
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin: 0 10px;
        }}
        .risk-fill {{
            height: 100%;
            background: linear-gradient(to right, #4caf50, #ff9800, #f44336);
            transition: width 0.3s;
        }}
        .recommendation-box {{
            background: #e8f5e9;
            border: 2px solid #4caf50;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
        }}
        .disclaimer {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px;
            border-radius: 4px;
            font-size: 0.9em;
            color: #856404;
        }}
    </style>
    
    <div class="report-header">
        <h1 class="report-title">{company_name} ({ticker})</h1>
        <p class="report-subtitle">AI 기반 투자 심리 분석 보고서</p>
        <p style="opacity: 0.8; font-size: 0.9em;">{datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}</p>
    </div>
    
    <!-- 점수 카드 -->
    <div class="score-card">
        <div class="score-value">{final_score:.1f}</div>
        <div class="score-label">투자 심리 점수</div>
        <div class="sentiment-badge">{self._get_sentiment_korean(sentiment)}</div>
    </div>
    
    <!-- 종합 분석 근거 -->
    <div class="evidence-summary">
        <h2 class="section-title">📋 종합 분석 근거</h2>
        {evidence_summary}
    </div>
    
    <!-- 데이터 수집 현황 -->
    <div class="section">
        <h2 class="section-title">📊 데이터 수집 현황</h2>
        <div class="data-grid">
            {self._generate_data_summary_cards(data_summary)}
        </div>
    </div>
    
    <!-- 정량적 지표 -->
    {self._generate_quantitative_section(quantitative_data)}
    
    <!-- 감정 분석 요약 -->
    <div class="section">
        <h2 class="section-title">🎯 감정 분석 요약</h2>
        {self._generate_sentiment_summary(sentiment_analysis, score_details)}
    </div>
    
    <!-- 리스크 분석 -->
    {self._generate_risk_section(risk_analysis)}
    
    <!-- 투자 권고사항 -->
    <div class="section">
        <h2 class="section-title">💡 투자 권고사항</h2>
        <div class="recommendation-box">
            {self._generate_recommendation(sentiment, final_score)}
        </div>
    </div>
    
    <!-- 종합 결론 -->
    <div class="conclusion-box">
        <h2 class="conclusion-title">📌 종합 결론</h2>
        <div class="conclusion-text">
            {self._generate_conclusion(ticker, final_score, sentiment, evidence_summary)}
        </div>
    </div>
    
    <div class="disclaimer">
        <strong>⚠️ 투자 유의사항</strong><br>
        본 보고서는 AI 기반 감정 분석 결과이며, 투자 결정의 참고 자료로만 활용하시기 바랍니다.
        실제 투자 결정 시에는 추가적인 재무 분석과 전문가 상담을 권장합니다.
    </div>
</div>
"""
        
        # 추천 메시지 생성
        recommendation = self._get_recommendation_message(sentiment, final_score)
        
        # 요약 생성
        summary = f"{company_name}({ticker})의 투자 심리 점수는 {final_score:.2f}점으로 {self._get_sentiment_korean(sentiment)} 수준입니다."
        
        logger.info(f"✅ 보고서 생성 완료 - 추천: {recommendation}")
        
        return {
            "report": report_html,
            "summary": summary,
            "recommendation": recommendation
        }
    
    def _get_score_color(self, score: float) -> str:
        """점수에 따른 색상 반환"""
        if score > 0.3:
            return "#4caf50"  # 긍정 - 녹색
        elif score < -0.3:
            return "#f44336"  # 부정 - 빨간색
        else:
            return "#ff9800"  # 중립 - 주황색
    
    def _get_sentiment_color(self, sentiment: str) -> str:
        """감정에 따른 색상 반환"""
        colors = {
            "positive": "#4caf50",  # 녹색
            "negative": "#d32f2f",  # 진한 빨간색
            "neutral": "#9e9e9e"    # 회색 (주황색에서 변경)
        }
        return colors.get(sentiment, "#757575")
    
    def _get_sentiment_korean(self, sentiment: str) -> str:
        """감정을 한국어로 변환"""
        translations = {
            "positive": "긍정적",
            "negative": "부정적",
            "neutral": "중립적"
        }
        return translations.get(sentiment, "중립적")
    
    def _generate_data_summary_cards(self, data_summary: Dict) -> str:
        """데이터 수집 현황 카드 생성"""
        cards = []
        icons = {"news": "📰", "twitter": "🐦", "sec": "📄"}
        
        for source, count in data_summary.items():
            icon = icons.get(source, "📊")
            cards.append(f"""
                <div class="data-card">
                    <div class="data-value">{icon} {count}</div>
                    <div class="data-label">{source.upper()}</div>
                </div>
            """)
        
        # 총계 카드 추가
        total = sum(data_summary.values())
        cards.append(f"""
            <div class="data-card">
                <div class="data-value">📊 {total}</div>
                <div class="data-label">전체</div>
            </div>
        """)
        
        return "".join(cards)
    
    def _generate_quantitative_section(self, quant_data: Dict) -> str:
        """정량적 지표 섹션 생성"""
        if not quant_data:
            return """
        <div class="section">
            <h2 class="section-title">📈 주요 정량적 지표</h2>
            <p style="color: #666;">정량적 분석 데이터를 수집 중입니다...</p>
        </div>
        """
        
        price_data = quant_data.get("price_data", {})
        tech_data = quant_data.get("technical_indicators", {})
        
        return f"""
        <div class="section">
            <h2 class="section-title">📈 주요 정량적 지표</h2>
            <div class="data-grid">
                <div class="data-card">
                    <div class="data-value">${price_data.get('current_price', 0):.2f}</div>
                    <div class="data-label">현재가</div>
                </div>
                <div class="data-card">
                    <div class="data-value" style="color: {self._get_score_color(price_data.get('day_change_percent', 0)/100)}">{price_data.get('day_change_percent', 0):+.2f}%</div>
                    <div class="data-label">일일 변동률</div>
                </div>
                <div class="data-card">
                    <div class="data-value">{tech_data.get('rsi', 50):.1f}</div>
                    <div class="data-label">RSI</div>
                </div>
                <div class="data-card">
                    <div class="data-value">{tech_data.get('macd_signal', 'N/A')}</div>
                    <div class="data-label">MACD 신호</div>
                </div>
            </div>
        </div>
        """
    
    def _generate_sentiment_summary(self, sentiment_analysis: List[Dict], score_details: Dict) -> str:
        """감정 분석 요약 생성"""
        if not sentiment_analysis:
            return "<p>감정 분석 데이터가 없습니다.</p>"
        
        # 전체 통계
        total_items = len(sentiment_analysis)
        positive_count = sum(1 for item in sentiment_analysis if item.get("score", 0) > 0.1)
        negative_count = sum(1 for item in sentiment_analysis if item.get("score", 0) < -0.1)
        neutral_count = total_items - positive_count - negative_count
        
        # 전체 요약
        html = [f"""
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 25px;">
                <h4 style="margin-bottom: 15px;">📊 전체 분석 요약</h4>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; text-align: center;">
                    <div style="background: #e8f5e9; padding: 15px; border-radius: 8px;">
                        <div style="font-size: 2em; font-weight: bold; color: #4caf50;">🟢 {positive_count}</div>
                        <div>긍정적 ({positive_count/total_items*100:.1f}%)</div>
                    </div>
                    <div style="background: #fff8e1; padding: 15px; border-radius: 8px;">
                        <div style="font-size: 2em; font-weight: bold; color: #ff9800;">🟡 {neutral_count}</div>
                        <div>중립적 ({neutral_count/total_items*100:.1f}%)</div>
                    </div>
                    <div style="background: #ffebee; padding: 15px; border-radius: 8px;">
                        <div style="font-size: 2em; font-weight: bold; color: #f44336;">🔴 {negative_count}</div>
                        <div>부정적 ({negative_count/total_items*100:.1f}%)</div>
                    </div>
                </div>
            </div>
        """]
        
        # 소스별 집계
        by_source = {}
        for item in sentiment_analysis:
            source = item.get("source", "unknown")
            if source not in by_source:
                by_source[source] = {"positive": 0, "negative": 0, "neutral": 0, "items": []}
            
            score = item.get("score", 0)
            if score > 0.1:
                by_source[source]["positive"] += 1
            elif score < -0.1:
                by_source[source]["negative"] += 1
            else:
                by_source[source]["neutral"] += 1
            
            by_source[source]["items"].append(item)
        
        # 주요 인사이트
        html.append("""
            <div style="margin-bottom: 25px;">
                <h4 style="margin-bottom: 15px;">🔍 주요 인사이트</h4>
        """)
        
        for source, data in by_source.items():
            source_icon = {"news": "📰", "twitter": "🐦", "sec": "📄"}.get(source, "📊")
            source_name = {"news": "뉴스", "twitter": "트위터", "sec": "SEC 공시"}.get(source, source.upper())
            total = len(data["items"])
            
            # 평균 점수 기반 감정 판단
            avg_score = sum(item.get("score", 0) for item in data["items"]) / len(data["items"]) if data["items"] else 0
            
            if avg_score > 0.3:
                dominant = "강한 긍정"
                color = "#4caf50"
            elif avg_score > 0.1:
                dominant = "긍정적"
                color = "#8bc34a"
            elif avg_score < -0.3:
                dominant = "강한 부정"
                color = "#f44336"
            elif avg_score < -0.1:
                dominant = "부정적"
                color = "#ff5722"
            else:
                # -0.1 ~ 0.1 사이
                if data['positive'] > data['negative']:
                    dominant = "약간 긍정"
                    color = "#9ccc65"
                elif data['negative'] > data['positive']:
                    dominant = "약간 부정"
                    color = "#ff7043"
                else:
                    dominant = "중립"
                    color = "#6c757d"
            
            html.append(f"""
                <div style="background: white; border: 1px solid #e0e0e0; padding: 20px; border-radius: 8px; margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                        <h5 style="margin: 0; font-size: 1.1em;">{source_icon} {source_name} ({total}건)</h5>
                        <span style="background: {color}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.9em;">
                            {dominant}
                        </span>
                    </div>
            """)
            
            # SEC 공시는 모든 항목 표시, 뉴스는 5개, 트위터는 3개
            if source == "sec":
                # SEC 공시는 점수순으로 정렬 (부정적인 것부터)
                display_items = sorted(data["items"], key=lambda x: x.get("score", 0))
            elif source == "news":
                # 뉴스는 상위 5개 항목 표시 (점수 절대값 기준)
                display_items = sorted(data["items"], key=lambda x: abs(x.get("score", 0)), reverse=True)[:5]
            else:
                # 트위터는 상위 3개 항목 표시
                display_items = sorted(data["items"], key=lambda x: abs(x.get("score", 0)), reverse=True)[:3]
            
            for i, item in enumerate(display_items):
                score = item.get("score", 0)
                
                # 점수 기반으로 감정 재계산
                if score > 0.1:
                    sentiment = "positive"
                elif score < -0.1:
                    sentiment = "negative"
                else:
                    sentiment = "neutral"
                
                # AI 요약 우선, 없으면 제목 사용
                ai_summary = item.get("summary", "")
                title = item.get("title_kr") or item.get("title", item.get("text", ""))
                
                # 표시할 내용 결정 (AI 요약 실패 시 제목 사용)
                if ai_summary and ai_summary != "분석 실패" and ai_summary != "요약 없음":
                    display_content = ai_summary
                else:
                    display_content = title
                    
                if len(display_content) > 200:
                    display_content = display_content[:197] + "..."
                
                sentiment_color = self._get_sentiment_color(sentiment)
                
                html.append(f"""
                    <div style="padding: 10px; margin: 8px 0; background: #f8f9fa; border-radius: 6px; 
                         border-left: 3px solid {sentiment_color};">
                        <div style="font-size: 0.85em; color: #666; margin-bottom: 5px;">
                            {self._get_sentiment_korean(sentiment)} (점수: {score:.2f})
                        </div>
                        <div style="color: #333; line-height: 1.4;">
                            {display_content}
                        </div>
                    </div>
                """)
            
            html.append("</div>")
        
        html.append("</div>")
        
        return "".join(html)
    
    def _generate_risk_section(self, risk_data: Dict) -> str:
        """리스크 분석 섹션 생성"""
        if not risk_data:
            return """
        <div class="section">
            <h2 class="section-title">⚠️ 리스크 분석</h2>
            <p style="color: #666;">리스크 분석 데이터를 수집 중입니다...</p>
        </div>
        """
        
        overall_risk = risk_data.get("overall_risk_score", 0)
        risk_level = risk_data.get("risk_level", "medium")
        
        risk_color = {
            "very_low": "#4caf50",
            "low": "#8bc34a",
            "medium": "#ff9800",
            "high": "#f44336",
            "very_high": "#d32f2f"
        }.get(risk_level, "#757575")
        
        risk_label_kr = {
            "very_low": "매우 낮음",
            "low": "낮음",
            "medium": "보통",
            "high": "높음",
            "very_high": "매우 높음"
        }.get(risk_level, "보통")
        
        # 개별 리스크 데이터
        market_risk = risk_data.get("market_risk", {})
        company_risk = risk_data.get("company_specific_risk", {})
        sentiment_risk = risk_data.get("sentiment_risk", {})
        liquidity_risk = risk_data.get("liquidity_risk", {})
        special_risks = risk_data.get("special_risks", {})
        
        # 특수 리스크 섹션 생성
        special_risk_html = ""
        if special_risks.get("score", 0) > 0:
            special_risk_html = self._generate_special_risks_section(special_risks)
        
        return f"""
        <div class="section">
            <h2 class="section-title">⚠️ 리스크 분석</h2>
            <div style="text-align: center; margin: 20px 0;">
                <div style="font-size: 2em; font-weight: bold; color: {risk_color}">
                    {risk_label_kr}
                </div>
                <div style="color: #666;">종합 리스크 수준</div>
            </div>
            
            <!-- 종합 리스크 -->
            <div class="risk-indicator">
                <span class="risk-label">종합 리스크</span>
                <div class="risk-bar">
                    <div class="risk-fill" style="width: {overall_risk}%"></div>
                </div>
                <span>{overall_risk:.0f}/100</span>
            </div>
            
            {special_risk_html}
            
            <!-- 개별 리스크 지표 -->
            <div style="margin-top: 20px;">
                <h4>세부 리스크 지표</h4>
                
                <div class="risk-indicator">
                    <span class="risk-label">시장 리스크</span>
                    <div class="risk-bar">
                        <div class="risk-fill" style="width: {market_risk.get('score', 50)}%"></div>
                    </div>
                    <span>{market_risk.get('score', 50):.0f}/100</span>
                </div>
                
                <div class="risk-indicator">
                    <span class="risk-label">기업 리스크</span>
                    <div class="risk-bar">
                        <div class="risk-fill" style="width: {company_risk.get('score', 50)}%"></div>
                    </div>
                    <span>{company_risk.get('score', 50):.0f}/100</span>
                </div>
                
                <div class="risk-indicator">
                    <span class="risk-label">감성 리스크</span>
                    <div class="risk-bar">
                        <div class="risk-fill" style="width: {sentiment_risk.get('score', 50)}%"></div>
                    </div>
                    <span>{sentiment_risk.get('score', 50):.0f}/100</span>
                </div>
                
                <div class="risk-indicator">
                    <span class="risk-label">유동성 리스크</span>
                    <div class="risk-bar">
                        <div class="risk-fill" style="width: {liquidity_risk.get('score', 30)}%"></div>
                    </div>
                    <span>{liquidity_risk.get('score', 30):.0f}/100</span>
                </div>
            </div>
            
            {self._generate_risk_recommendations(risk_data.get("recommendations", []))}
        </div>
        """
    
    def _generate_special_risks_section(self, special_risks: Dict) -> str:
        """특수 리스크 섹션 생성"""
        risk_types = special_risks.get("risk_types", {})
        if not risk_types:
            return ""
        
        risk_items = []
        for risk_type, score in risk_types.items():
            if score > 0:
                risk_name_kr = {
                    "owner_risk": "오너/경영진 리스크",
                    "regulatory_risk": "규제 리스크",
                    "competition_risk": "경쟁 리스크",
                    "management_risk": "경영진 리스크",
                    "metaverse_risk": "메타버스 리스크"
                }.get(risk_type, risk_type.replace("_", " ").title())
                
                # 리스크 수준에 따른 색상
                if score > 60:
                    color = "#f44336"  # 빨강
                elif score > 40:
                    color = "#ff9800"  # 주황
                else:
                    color = "#ffc107"  # 노랑
                
                risk_items.append(f"""
                    <div class="risk-indicator">
                        <span class="risk-label" style="font-weight: bold; color: {color};">⚡ {risk_name_kr}</span>
                        <div class="risk-bar">
                            <div class="risk-fill" style="width: {score}%; background: {color};"></div>
                        </div>
                        <span style="color: {color};">{score:.0f}/100</span>
                    </div>
                """)
        
        if risk_items:
            return f"""
                <div style="margin-top: 20px; background: #fff3cd; padding: 15px; border-radius: 8px; border: 1px solid #ffeaa7;">
                    <h4 style="color: #856404; margin-bottom: 10px;">🎯 특수 리스크 요인</h4>
                    {"".join(risk_items)}
                    <div style="margin-top: 10px; color: #666; font-size: 0.9em;">
                        * 기업별 특수 상황에 따른 추가 리스크 요인
                    </div>
                </div>
            """
        
        return ""
    
    def _generate_risk_recommendations(self, recommendations: List) -> str:
        """리스크 관련 권고사항 생성"""
        if not recommendations:
            return ""
        
        items = []
        for rec in recommendations[:5]:  # 최대 5개
            if isinstance(rec, dict):
                priority = rec.get("priority", "medium")
                priority_color = {
                    "high": "#f44336",
                    "medium": "#ff9800",
                    "low": "#4caf50"
                }.get(priority, "#757575")
                
                priority_kr = {
                    "high": "높음",
                    "medium": "보통",
                    "low": "낮음"
                }.get(priority, "보통")
                
                action = rec.get("action", "")
                reason = rec.get("reason", "")
                
                items.append(f"""
                    <li style="margin-bottom: 10px;">
                        <span style="color: {priority_color}; font-weight: bold;">[{priority_kr}]</span>
                        <strong>{action}</strong>: {reason}
                    </li>
                """)
            else:
                items.append(f"<li>{rec}</li>")
        
        return f"""
            <div style="margin-top: 20px; background: #f8f9fa; padding: 15px; border-radius: 8px;">
                <h4>📋 리스크 관리 권고사항</h4>
                <ul style="line-height: 1.8; list-style: none; padding-left: 0;">
                    {"".join(items)}
                </ul>
            </div>
        """
    
    def _generate_recommendation(self, sentiment: str, score: float) -> str:
        """투자 권고사항 생성"""
        if sentiment == "positive" or score > 0.3:
            return """
                <p><strong>📈 긍정적 투자 심리</strong></p>
                <ul style="line-height: 1.8; margin-top: 10px;">
                    <li>현재 시장 심리가 긍정적으로 나타나고 있습니다.</li>
                    <li>단기적으로 상승 모멘텀이 있을 수 있으나, 과도한 낙관은 경계하세요.</li>
                    <li>분산 투자를 통해 리스크를 관리하시기 바랍니다.</li>
                </ul>
            """
        elif sentiment == "negative" or score < -0.3:
            return """
                <p><strong>📉 부정적 투자 심리</strong></p>
                <ul style="line-height: 1.8; margin-top: 10px;">
                    <li>현재 시장 심리가 부정적으로 나타나고 있습니다.</li>
                    <li>추가 하락 가능성을 염두에 두고 신중하게 접근하세요.</li>
                    <li>장기 투자 관점에서는 저가 매수 기회일 수 있습니다.</li>
                </ul>
            """
        else:
            return """
                <p><strong>↔️ 중립적 투자 심리</strong></p>
                <ul style="line-height: 1.8; margin-top: 10px;">
                    <li>현재 시장 심리가 중립적으로 나타나고 있습니다.</li>
                    <li>명확한 방향성이 나타날 때까지 관망하는 것이 좋습니다.</li>
                    <li>추가적인 시장 신호를 주시하며 대응하세요.</li>
                </ul>
            """
    
    def _get_recommendation_message(self, sentiment: str, score: float) -> str:
        """간단한 추천 메시지 생성"""
        if sentiment == "positive" or score > 0.3:
            return "매수 고려 - 긍정적인 시장 심리를 보이고 있습니다."
        elif sentiment == "negative" or score < -0.3:
            return "매도 고려 - 부정적인 시장 심리를 보이고 있습니다."
        else:
            return "관망 추천 - 중립적인 시장 심리를 보이고 있으며, 추가적인 모니터링이 필요합니다."
    
    async def _broadcast_report_generated(self, ticker: str, report_data: Dict):
        """리포트 생성 완료 이벤트 브로드캐스트"""
        event_data = {
            "ticker": ticker,
            "report": report_data.get("report", ""),
            "summary": report_data.get("summary", ""),
            "recommendation": report_data.get("recommendation", ""),
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_event("report_generated", event_data)
        logger.info(f"📢 보고서 생성 이벤트 브로드캐스트: {ticker}")
    
    def _analyze_evidence(self, sentiment_analysis: List[Dict], data_summary: Dict) -> str:
        """데이터 근거 분석 및 요약"""
        evidence_html = []
        
        # 빈 데이터 처리
        if not sentiment_analysis:
            return "<p>⚠️ 분석할 감정 데이터가 없습니다.</p>"
        
        # 소스별 데이터 그룹화
        by_source = {}
        for item in sentiment_analysis:
            if not item:  # None 또는 빈 딕셔너리 체크
                continue
            source = item.get('source', 'unknown')
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(item)
        
        # 각 소스별 분석
        for source, items in by_source.items():
            source_name = {
                'news': '📰 뉴스',
                'twitter': '🐦 트위터', 
                'sec': '📄 SEC 공시'
            }.get(source, source)
            
            evidence_html.append(f'<h4>{source_name} ({len(items)}건)</h4>')
            
            if source == 'news':
                evidence_html.append('<ul>')
                for item in items[:5]:  # 상위 5개
                    # AI 분석 요약 가져오기
                    ai_summary = item.get('summary', '')  # AI가 분석한 요약
                    title = item.get('title_kr') or item.get('title', '') or item.get('text', '')[:100]
                    
                    score = item.get('score', 0)
                    sentiment = '긍정' if score > 0.1 else '부정' if score < -0.1 else '중립'
                    sentiment_color = '#28a745' if score > 0.1 else '#dc3545' if score < -0.1 else '#6c757d'
                    
                    # URL과 시간 정보 추가
                    url = item.get('url', '')
                    published_date = item.get('published_date', '')
                    source_name = item.get('source', 'Unknown')
                    
                    # AI 요약이 없거나 실패한 경우 제목 사용
                    if ai_summary and ai_summary != "분석 실패" and ai_summary != "요약 없음":
                        display_content = ai_summary
                    else:
                        display_content = title
                    
                    if len(display_content) > 200:
                        display_content = display_content[:197] + "..."
                    
                    # 제목은 작게 표시 (참고용)
                    short_title = title if len(title) <= 80 else title[:77] + "..."
                    
                    evidence_html.append(f'''
                        <li style="margin-bottom: 15px;">
                            <div style="color: {sentiment_color}; font-weight: bold; line-height: 1.4;">
                                [{sentiment}] {display_content}
                            </div>
                            <div style="color: #888; font-size: 0.85em; margin-top: 5px; font-style: italic;">
                                📰 {short_title}
                            </div>
                            <div style="color: #999; font-size: 0.85em; margin-top: 3px;">
                                출처: {source_name}
                                {f' | <a href="{url}" target="_blank" style="color: #0066cc;">원문 보기</a>' if url else ''}
                                {f' | {published_date[:10]}' if published_date else ''}
                            </div>
                        </li>
                    ''')
                evidence_html.append('</ul>')
                
            elif source == 'twitter':
                positive = len([i for i in items if i.get('score', 0) > 0.1])
                negative = len([i for i in items if i.get('score', 0) < -0.1])
                neutral = len([i for i in items if -0.1 <= i.get('score', 0) <= 0.1])
                
                if len(items) > 0:
                    evidence_html.append(f'<p>감정 분포: 긍정 {positive}건, 부정 {negative}건, 중립 {neutral}건</p>')
                    evidence_html.append('<ul>')
                    for item in items[:3]:
                        text = item.get('text', '')
                        score = item.get('score', 0)
                        sentiment = '긍정' if score > 0.1 else '부정' if score < -0.1 else '중립'
                        sentiment_color = '#28a745' if score > 0.1 else '#dc3545' if score < -0.1 else '#6c757d'
                        # 트윗 URL 및 작성 시간 추가
                        url = item.get('url', '')
                        created_at = item.get('created_at', '')
                        author = item.get('author', '')
                        
                        evidence_html.append(f'''
                            <li style="margin-bottom: 10px;">
                                <div style="color: {sentiment_color};">[{sentiment}] {text}</div>
                                <div style="color: #999; font-size: 0.85em; margin-top: 3px;">
                                    @{author}
                                    {f' | <a href="{url}" target="_blank" style="color: #0066cc;">트윗 보기</a>' if url else ''}
                                    {f' | {created_at[:16]}' if created_at else ''}
                                </div>
                            </li>
                        ''')
                    evidence_html.append('</ul>')
                else:
                    evidence_html.append('<p style="color: #999;">트위터 데이터 수집 실패 (API 제한)</p>')
                
            elif source == 'sec':
                evidence_html.append('<ul>')
                # SEC 공시는 모든 항목 표시 (최대 20개)
                for item in items[:20]:
                    # SEC 공시 정보 추출
                    form_type = item.get('form_type', 'Unknown')
                    filing_date = item.get('filing_date', '')
                    title = item.get('title_kr') or item.get('title', '') or item.get('text', '')
                    content = item.get('content', '')
                    
                    # 공시 타입별 한글 설명
                    form_descriptions = {
                        '10-K': '연간 보고서 - 회사의 연간 실적 및 재무상태',
                        '10-Q': '분기 보고서 - 분기별 실적 및 경영 현황',
                        '8-K': '임시 보고서 - 주요 이벤트 및 경영상 중요 변경사항',
                        '4': '내부자 거래 - 임원진의 주식 매매 내역',
                        'DEF 14A': '주주총회 위임장 - 주주총회 안건 및 임원 보수',
                        '144': '제한 주식 매도 신고 - 내부자의 주식 매도 계획'
                    }
                    
                    form_desc = form_descriptions.get(form_type, '기타 공시')
                    score = item.get('score', 0)
                    sentiment = '긍정' if score > 0.1 else '부정' if score < -0.1 else '중립'
                    sentiment_color = '#28a745' if score > 0.1 else '#dc3545' if score < -0.1 else '#6c757d'
                    
                    # SEC 공시 URL 추가
                    url = item.get('url', '')
                    extracted_info = item.get('extracted_info', {})
                    
                    # AI 분석 요약 가져오기
                    ai_summary = item.get('summary', '')
                    
                    evidence_html.append(f'''
                        <li style="margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid {sentiment_color};">
                            <div style="font-weight: bold; font-size: 1.1em; margin-bottom: 8px;">
                                <span style="color: #0066cc;">[{form_type}]</span> {form_desc}
                            </div>
                            <div style="color: #333; margin: 8px 0; font-size: 0.95em;">
                                <strong>{form_type} 공시 ({filing_date[:10] if filing_date else "날짜 없음"})</strong>
                            </div>
                            <div style="color: #666; margin: 8px 0; line-height: 1.5;">
                                {title}
                                {f'<br/><div style="margin-top: 8px; padding: 10px; background: #e9ecef; border-radius: 4px;"><strong>내용:</strong> {content}</div>' if content and len(content) > 10 else ''}
                            </div>
                            {f'<div style="margin-top: 10px; padding: 10px; background: #fff; border: 1px solid #dee2e6; border-radius: 4px;"><strong>AI 분석:</strong> {ai_summary}</div>' if ai_summary and ai_summary != "분석 실패" else ''}
                            <div style="color: #999; font-size: 0.85em; margin-top: 10px;">
                                <strong>공시일:</strong> {filing_date} 
                                {f' | <a href="{url}" target="_blank" style="color: #0066cc; text-decoration: none;"><strong>SEC 문서 보기</strong></a>' if url else ''}
                                | <strong>감정:</strong> <span style="color: {sentiment_color}; font-weight: bold;">{sentiment}</span>
                            </div>
                        </li>
                    ''')
                evidence_html.append('</ul>')
        
        return ''.join(evidence_html)
    
    def _translate_to_korean(self, title: str, content: str) -> str:
        """간단한 키워드 기반 한글 번역"""
        # 주요 키워드 매핑
        translations = {
            'earnings': '실적', 'revenue': '매출', 'profit': '이익', 'loss': '손실',
            'growth': '성장', 'decline': '하락', 'increase': '증가', 'decrease': '감소',
            'strong': '강한', 'weak': '약한', 'positive': '긍정적', 'negative': '부정적',
            'sales': '판매', 'margin': '마진', 'guidance': '가이던스', 'forecast': '전망',
            'beat': '상회', 'miss': '하회', 'expects': '예상', 'announces': '발표',
            'launches': '출시', 'partnership': '파트너십', 'acquisition': '인수',
            'investment': '투자', 'expansion': '확장', 'dividend': '배당',
            'stock': '주식', 'share': '주가', 'market': '시장', 'quarter': '분기',
            'year': '연도', 'annual': '연간', 'quarterly': '분기별'
        }
        
        text = (title + ' ' + content).lower()
        
        # 간단한 문맥 기반 번역
        if 'earnings beat' in text or 'beats earnings' in text:
            return "📈 실적이 시장 예상치를 상회했습니다"
        elif 'earnings miss' in text or 'misses earnings' in text:
            return "📉 실적이 시장 예상치를 하회했습니다"
        elif 'revenue growth' in text:
            return "💰 매출이 성장세를 보이고 있습니다"
        elif 'profit increase' in text or 'profit rise' in text:
            return "💵 이익이 증가했습니다"
        elif 'new product' in text or 'launches' in text:
            return "🚀 신제품 출시 관련 소식입니다"
        elif 'partnership' in text or 'collaboration' in text:
            return "🤝 파트너십/협력 관련 소식입니다"
        elif 'acquisition' in text or 'merger' in text:
            return "🏢 인수합병 관련 소식입니다"
        elif 'expansion' in text:
            return "🌍 사업 확장 관련 소식입니다"
        elif 'dividend' in text:
            return "💸 배당 관련 소식입니다"
        elif 'layoff' in text or 'job cut' in text:
            return "👥 인력 감축 관련 소식입니다"
        elif 'lawsuit' in text or 'legal' in text:
            return "⚖️ 법적 이슈 관련 소식입니다"
        else:
            # 키워드 기반 간단 번역
            result = []
            for eng, kor in translations.items():
                if eng in text:
                    result.append(kor)
            
            if result:
                return f"📊 {', '.join(result[:3])} 관련 소식"
            else:
                return "📰 기업 관련 일반 뉴스"
            
    
    def _extract_keywords(self, items: List[Dict]) -> str:
        """주요 키워드 추출"""
        # 실제 제목에서 주요 내용 추출
        titles = []
        for item in items[:3]:  # 상위 3개만
            title = item.get("title_kr") or item.get("title", item.get("text", ""))
            if title:
                # 길이 제한
                if len(title) > 50:
                    title = title[:47] + "..."
                titles.append(title)
        
        if titles:
            return " | ".join(titles)
        return "데이터 분석 중"
    
    def _generate_conclusion(self, ticker: str, score: float, sentiment: str, evidence_summary: str) -> str:
        """종합 결론 생성"""
        # 근거 데이터 개수 계산 (각 소스의 데이터 개수 추출)
        import re
        news_match = re.search(r'뉴스.*?(\d+)건', evidence_summary)
        twitter_match = re.search(r'트위터.*?(\d+)건', evidence_summary)
        sec_match = re.search(r'SEC.*?(\d+)건', evidence_summary)
        
        news_count = int(news_match.group(1)) if news_match else 0
        twitter_count = int(twitter_match.group(1)) if twitter_match else 0
        sec_count = int(sec_match.group(1)) if sec_match else 0
        total_count = news_count + twitter_count + sec_count
        
        # 주요 데이터 소스 판단
        main_sources = []
        if news_count > 0:
            main_sources.append(f"뉴스 {news_count}건")
        if twitter_count > 0:
            main_sources.append(f"트위터 {twitter_count}건")
        if sec_count > 0:
            main_sources.append(f"SEC 공시 {sec_count}건")
        
        sources_text = ", ".join(main_sources)
        
        if sentiment == "positive" or score > 0.3:
            conclusion = f"""
                <div style="margin-bottom: 15px;">
                    <strong>📊 분석 데이터:</strong> 총 {total_count}건 ({sources_text})
                </div>
                
                <div style="margin-bottom: 15px;">
                    <strong>🎯 핵심 판단:</strong> {ticker}에 대한 시장 심리는 <strong style="color: #4caf50;">긍정적</strong>입니다.
                </div>
                
                <div style="margin-bottom: 15px;">
                    <strong>💼 투자 시사점:</strong><br>
                    • 시장에서는 {ticker}의 성장 가능성을 높게 평가하고 있습니다<br>
                    • 투자자들의 매수 심리가 강하게 형성되어 있습니다<br>
                    • 단기적으로 상승 모멘텀이 지속될 가능성이 높습니다
                </div>
                
                <div>
                    <strong>⚠️ 유의사항:</strong> 종합 점수 <strong>{score:.1f}점</strong>은 현재 시점의 시장 심리를 반영한 것으로,
                    과도한 낙관은 경계하시고 분산 투자를 권장합니다.
                </div>
            """
        elif sentiment == "negative" or score < -0.3:
            conclusion = f"""
                <div style="margin-bottom: 15px;">
                    <strong>📊 분석 데이터:</strong> 총 {total_count}건 ({sources_text})
                </div>
                
                <div style="margin-bottom: 15px;">
                    <strong>🎯 핵심 판단:</strong> {ticker}에 대한 시장 심리는 <strong style="color: #f44336;">부정적</strong>입니다.
                </div>
                
                <div style="margin-bottom: 15px;">
                    <strong>💼 투자 시사점:</strong><br>
                    • 시장에서 {ticker}에 대한 우려가 확산되고 있습니다<br>
                    • 투자자들의 리스크 회피 심리가 강화되고 있습니다<br>
                    • 단기적으로 조정 국면이 지속될 가능성이 있습니다
                </div>
                
                <div>
                    <strong>⚠️ 유의사항:</strong> 종합 점수 <strong>{score:.1f}점</strong>은 현재의 부정적 시장 심리를 반영하며,
                    손실 방어에 중점을 두고 리스크 관리를 강화하시기 바랍니다.
                </div>
            """
        else:
            conclusion = f"""
                <div style="margin-bottom: 15px;">
                    <strong>📊 분석 데이터:</strong> 총 {total_count}건 ({sources_text})
                </div>
                
                <div style="margin-bottom: 15px;">
                    <strong>🎯 핵심 판단:</strong> {ticker}에 대한 시장 심리는 <strong style="color: #ff9800;">중립적</strong>입니다.
                </div>
                
                <div style="margin-bottom: 15px;">
                    <strong>💼 투자 시사점:</strong><br>
                    • 시장에서 {ticker}에 대한 의견이 분분한 상황입니다<br>
                    • 긍정과 부정 요인이 균형을 이루고 있습니다<br>
                    • 추가적인 시장 신호를 기다리는 관망세가 우세합니다
                </div>
                
                <div>
                    <strong>⚠️ 유의사항:</strong> 종합 점수 <strong>{score:.1f}점</strong>은 시장의 불확실성을 반영하며,
                    신중한 접근과 추가적인 정보 수집을 권장합니다.
                </div>
            """
        
        return conclusion
    
    # PDF 생성 기능은 브라우저에서 처리
    # async def _save_report_as_pdf(self, ticker: str, html_content: str, company_name: Optional[str] = None) -> Path:
        """HTML 리포트를 PDF로 저장"""
        try:
            # PDF 저장 디렉토리 생성
            pdf_dir = Path("reports/pdf")
            pdf_dir.mkdir(parents=True, exist_ok=True)
            
            # 파일명 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{ticker}_report_{timestamp}.pdf"
            pdf_path = pdf_dir / filename
            
            # HTML에 추가 스타일 적용 (PDF 최적화)
            pdf_optimized_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>{ticker} Investment Analysis Report</title>
                <style>
                    @page {{
                        size: A4;
                        margin: 2cm;
                    }}
                    body {{
                        font-family: 'Helvetica Neue', Arial, sans-serif;
                        font-size: 11pt;
                        line-height: 1.6;
                        color: #333;
                    }}
                    /* PDF에서 더 나은 렌더링을 위한 스타일 조정 */
                    .report-header {{
                        page-break-after: avoid;
                    }}
                    .section {{
                        page-break-inside: avoid;
                        margin-bottom: 20px;
                    }}
                    table {{
                        page-break-inside: avoid;
                    }}
                    /* 그라디언트 대신 단색 사용 */
                    .score-card {{
                        background: #f5f5f5 !important;
                    }}
                    .evidence-summary {{
                        background: #f5f7fa !important;
                    }}
                    .conclusion-box {{
                        background: #667eea !important;
                    }}
                </style>
            </head>
            <body>
                {html_content}
                <div style="margin-top: 50px; font-size: 10pt; color: #666; text-align: center;">
                    <p>이 보고서는 {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}에 생성되었습니다.</p>
                    <p>A2A AI 투자 분석 시스템 v2.0</p>
                </div>
            </body>
            </html>
            """
            
            # PDF 생성
            pdf_document = weasyprint.HTML(string=pdf_optimized_html).render()
            pdf_bytes = pdf_document.write_pdf()
            
            # PDF 파일 저장
            with open(pdf_path, 'wb') as f:
                f.write(pdf_bytes)
            
            logger.info(f"✅ PDF 저장 완료: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            logger.error(f"❌ PDF 저장 오류: {e}")
            raise HTTPException(status_code=500, detail=f"PDF 생성 중 오류 발생: {str(e)}")
    
    async def _generate_pdf_content(self, html_content: str) -> bytes:
        """HTML을 PDF 바이트로 변환"""
        try:
            # HTML에 추가 스타일 적용 (PDF 최적화)
            pdf_optimized_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    @page {{
                        size: A4;
                        margin: 2cm;
                    }}
                    body {{
                        font-family: 'Helvetica Neue', Arial, sans-serif;
                        font-size: 11pt;
                        line-height: 1.6;
                        color: #333;
                    }}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            
            # PDF 생성
            pdf_document = weasyprint.HTML(string=pdf_optimized_html).render()
            return pdf_document.write_pdf()
            
        except Exception as e:
            logger.error(f"❌ PDF 생성 오류: {e}")
            raise HTTPException(status_code=500, detail=f"PDF 생성 중 오류 발생: {str(e)}")
    
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
    uvicorn.run(app, host="0.0.0.0", port=8004)