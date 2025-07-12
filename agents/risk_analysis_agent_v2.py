"""
리스크 분석 에이전트 V2 - A2A 프로토콜 기반
종합적인 리스크 지표를 분석하고 포트폴리오 관점의 리스크 평가를 제공
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from scipy import stats

from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from pydantic import BaseModel

from a2a_core.base.base_agent import BaseAgent
from a2a_core.protocols.message import A2AMessage, MessageType

# 설정 관리자 및 커스텀 에러 임포트
from utils.config_manager import config
from utils.errors import RiskAnalysisError, DataNotFoundError
from utils.auth import verify_api_key

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiskAnalysisAgentV2(BaseAgent):
    """리스크 분석 전문 A2A 에이전트"""
    
    def __init__(self):
        # 설정에서 에이전트 정보 가져오기
        agent_config = config.get_agent_config("risk_analysis")
        
        super().__init__(
            name=agent_config.get("name", "Risk Analysis Agent V2"),
            description="종합적인 리스크 지표 분석 및 포트폴리오 리스크 평가 A2A 에이전트",
            port=agent_config.get("port", 8212)
        )
        
        # 타임아웃 설정
        self.timeout = agent_config.get("timeout", 60)
        
        # 리스크 가중치 설정
        risk_weights = config.get("risk_weights", {})
        self.risk_weights = {
            "market": risk_weights.get("market", 0.25),
            "company": risk_weights.get("company", 0.25),
            "sentiment": risk_weights.get("sentiment", 0.20),
            "liquidity": risk_weights.get("liquidity", 0.10),
            "special": risk_weights.get("special", 0.20)
        }
        
        self.capabilities = [
            {
                "name": "risk_analysis",
                "version": "2.0",
                "description": "종합적인 투자 리스크 분석",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string", "description": "주식 티커"},
                        "price_data": {"type": "object", "description": "가격 데이터"},
                        "technical_indicators": {"type": "object", "description": "기술적 지표"},
                        "sentiment_data": {"type": "array", "description": "감성 분석 결과"},
                        "market_data": {"type": "object", "description": "시장 데이터 (선택)"}
                    },
                    "required": ["ticker"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "market_risk": {"type": "object"},
                        "company_specific_risk": {"type": "object"},
                        "sentiment_risk": {"type": "object"},
                        "liquidity_risk": {"type": "object"},
                        "overall_risk_score": {"type": "number"},
                        "risk_level": {"type": "string"},
                        "recommendations": {"type": "array"}
                    }
                }
            }
        ]
        
        # HTTP 엔드포인트 추가
        self._setup_http_endpoints()
    
    def _setup_http_endpoints(self):
        """HTTP 엔드포인트 설정"""
        from pydantic import BaseModel
        from typing import Optional
        
        class RiskAnalysisRequest(BaseModel):
            ticker: str
            price_data: Optional[Dict] = None
            technical_indicators: Optional[Dict] = None
            sentiment_data: Optional[List] = None
            quantitative_data: Optional[Dict] = None
        
        @self.app.post("/risk_analysis", dependencies=[Depends(verify_api_key)])
        async def risk_analysis(request: RiskAnalysisRequest):
            """HTTP 엔드포인트로 리스크 분석 수행"""
            logger.info(f"⚠️ HTTP 요청으로 리스크 분석: {request.ticker}")
            
            # quantitative_data가 있으면 분해해서 사용
            price_data = request.price_data
            technical_indicators = request.technical_indicators
            
            if request.quantitative_data:
                price_data = request.quantitative_data.get("price_data", {})
                technical_indicators = request.quantitative_data.get("technical_indicators", {})
            
            # 종합 리스크 분석 수행
            analysis_result = await self._analyze_comprehensive_risk(
                ticker=request.ticker,
                price_data=price_data,
                technical_indicators=technical_indicators,
                sentiment_data=request.sentiment_data or [],
                market_data={}
            )
            
            return {
                "ticker": request.ticker,
                "risk_analysis": analysis_result,
                "analysis_date": datetime.now().isoformat()
            }
    
    async def handle_message(self, message: A2AMessage):
        """메시지 처리"""
        try:
            logger.info(f"🔍 메시지 수신 - Type: {message.header.message_type}, Action: {message.body.get('action') if message.body else None}")
            
            # 이벤트 메시지는 무시
            if message.header.message_type == MessageType.EVENT:
                return
            
            # 요청 메시지 처리
            if message.header.message_type == MessageType.REQUEST and message.body.get("action") == "risk_analysis":
                payload = message.body.payload
                ticker = payload.get("ticker")
                
                if not ticker:
                    await self.send_response(
                        message,
                        self.create_response(
                            request_message=message,
                            success=False,
                            error="티커가 제공되지 않았습니다"
                        )
                    )
                    return
                
                logger.info(f"🎯 리스크 분석 시작: {ticker}")
                
                # 종합 리스크 분석 수행
                risk_analysis = await self._analyze_comprehensive_risk(
                    ticker,
                    payload.get("price_data", {}),
                    payload.get("technical_indicators", {}),
                    payload.get("sentiment_data", []),
                    payload.get("market_data", {})
                )
                
                # 응답 전송
                response_data = {
                    "ticker": ticker,
                    "analysis_date": datetime.now().isoformat(),
                    **risk_analysis
                }
                
                # 이벤트 브로드캐스트
                await self._broadcast_risk_analysis_complete(ticker, risk_analysis)
                
                # 응답 전송
                await self.reply_to_message(
                    original_message=message,
                    result=response_data,
                    success=True
                )
                
        except Exception as e:
            logger.error(f"❌ 리스크 분석 실패: {str(e)}")
            await self.reply_to_message(
                original_message=message,
                result={"error": str(e)},
                success=False
            )
    
    async def _analyze_comprehensive_risk(
        self, 
        ticker: str, 
        price_data: Dict,
        technical_indicators: Dict,
        sentiment_data: List,
        market_data: Dict
    ) -> Dict:
        """종합적인 리스크 분석"""
        try:
            # 1. 시장 리스크 분석
            market_risk = self._analyze_market_risk(price_data, technical_indicators, market_data)
            
            # 2. 기업 고유 리스크 분석
            company_risk = self._analyze_company_specific_risk(
                price_data, technical_indicators, sentiment_data
            )
            
            # 3. 감성 기반 리스크 분석
            sentiment_risk = self._analyze_sentiment_risk(sentiment_data)
            
            # 4. 유동성 리스크 분석
            liquidity_risk = self._analyze_liquidity_risk(price_data)
            
            # 5. 특수 리스크 분석 (오너 리스크, 규제 리스크 등)
            special_risks = self._analyze_special_risks(ticker, sentiment_data)
            
            # 6. 종합 리스크 점수 계산 (특수 리스크 포함)
            overall_score, risk_level = self._calculate_overall_risk_with_special(
                market_risk, company_risk, sentiment_risk, liquidity_risk, special_risks
            )
            
            # 7. 리스크 완화 권고사항 생성
            recommendations = self._generate_risk_recommendations_enhanced(
                overall_score, market_risk, company_risk, sentiment_risk, liquidity_risk, special_risks
            )
            
            return {
                "market_risk": market_risk,
                "company_specific_risk": company_risk,
                "sentiment_risk": sentiment_risk,
                "liquidity_risk": liquidity_risk,
                "special_risks": special_risks,
                "overall_risk_score": overall_score,
                "risk_level": risk_level,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"종합 리스크 분석 오류: {str(e)}")
            return self._get_default_risk_analysis()
    
    def _analyze_market_risk(self, price_data: Dict, technical: Dict, market: Dict) -> Dict:
        """시장 리스크 분석"""
        try:
            # 베타 값 (시장 대비 변동성)
            beta = technical.get("beta", 1.0) if technical else 1.0
            
            # 시장 상관관계
            correlation = market.get("market_correlation", 0.7) if market else 0.7
            
            # 섹터 리스크 (임시값)
            sector_volatility = market.get("sector_volatility", 0.25) if market else 0.25
            
            # VIX 연동성 (시장 공포 지수)
            vix_sensitivity = self._calculate_vix_sensitivity(beta, correlation)
            
            # 시장 리스크 점수 (0-100)
            market_risk_score = min(100, (
                beta * 30 +  # 베타의 영향
                correlation * 20 +  # 시장 상관관계
                sector_volatility * 100 * 25 +  # 섹터 변동성
                vix_sensitivity * 25  # VIX 민감도
            ))
            
            return {
                "score": round(market_risk_score, 2),
                "beta": round(beta, 2),
                "market_correlation": round(correlation, 2),
                "sector_volatility": round(sector_volatility * 100, 2),
                "vix_sensitivity": round(vix_sensitivity, 2),
                "level": self._get_risk_level(market_risk_score),
                "factors": self._get_market_risk_factors(beta, correlation, sector_volatility)
            }
        except Exception as e:
            logger.error(f"시장 리스크 분석 오류: {str(e)}")
            return {"score": 50, "level": "medium", "factors": []}
    
    def _analyze_company_specific_risk(self, price_data: Dict, technical: Dict, sentiment: List) -> Dict:
        """기업 고유 리스크 분석"""
        try:
            # 가격 변동성
            volatility = technical.get("volatility", {}).get("annual", 0.3) if technical else 0.3
            
            # 최대 낙폭
            max_drawdown = abs(technical.get("max_drawdown", -0.2)) if technical else 0.2
            
            # 감성 분산도 (의견 일치도)
            sentiment_variance = self._calculate_sentiment_variance(sentiment)
            
            # 뉴스 부정 비율
            negative_ratio = self._calculate_negative_sentiment_ratio(sentiment)
            
            # 기업 리스크 점수
            company_risk_score = min(100, (
                volatility * 100 * 0.3 +  # 변동성
                max_drawdown * 100 * 0.3 +  # 최대 낙폭
                sentiment_variance * 100 * 0.2 +  # 의견 분산
                negative_ratio * 100 * 0.2  # 부정적 여론
            ))
            
            return {
                "score": round(company_risk_score, 2),
                "volatility": round(volatility * 100, 2),
                "max_drawdown": round(max_drawdown * 100, 2),
                "sentiment_variance": round(sentiment_variance, 2),
                "negative_ratio": round(negative_ratio * 100, 2),
                "level": self._get_risk_level(company_risk_score),
                "factors": self._get_company_risk_factors(
                    volatility, max_drawdown, sentiment_variance, negative_ratio
                )
            }
        except Exception as e:
            logger.error(f"기업 리스크 분석 오류: {str(e)}")
            return {"score": 50, "level": "medium", "factors": []}
    
    def _analyze_sentiment_risk(self, sentiment_data: List) -> Dict:
        """감성 기반 리스크 분석"""
        try:
            if not sentiment_data:
                return {"score": 50, "level": "medium", "factors": []}
            
            # 감성 점수 추출
            scores = [item.get("score", 0) for item in sentiment_data if "score" in item]
            
            if not scores:
                return {"score": 50, "level": "medium", "factors": []}
            
            # 평균 감성 점수
            avg_sentiment = np.mean(scores)
            
            # 감성 변동성
            sentiment_std = np.std(scores) if len(scores) > 1 else 0
            
            # 극단적 부정 의견 비율
            extreme_negative = sum(1 for s in scores if s < -0.5) / len(scores)
            
            # 소스별 불일치도
            source_disagreement = self._calculate_source_disagreement(sentiment_data)
            
            # 감성 리스크 점수
            sentiment_risk_score = min(100, (
                max(0, -avg_sentiment) * 50 * 0.3 +  # 부정적 감성
                sentiment_std * 100 * 0.3 +  # 의견 불일치
                extreme_negative * 100 * 0.2 +  # 극단적 부정
                source_disagreement * 100 * 0.2  # 소스간 불일치
            ))
            
            return {
                "score": round(sentiment_risk_score, 2),
                "average_sentiment": round(avg_sentiment, 2),
                "sentiment_volatility": round(sentiment_std, 2),
                "extreme_negative_ratio": round(extreme_negative * 100, 2),
                "source_disagreement": round(source_disagreement, 2),
                "level": self._get_risk_level(sentiment_risk_score),
                "factors": self._get_sentiment_risk_factors(
                    avg_sentiment, sentiment_std, extreme_negative
                )
            }
        except Exception as e:
            logger.error(f"감성 리스크 분석 오류: {str(e)}")
            return {"score": 50, "level": "medium", "factors": []}
    
    def _analyze_liquidity_risk(self, price_data: Dict) -> Dict:
        """유동성 리스크 분석"""
        try:
            # 거래량 데이터
            volume = price_data.get("volume", 0)
            avg_volume = price_data.get("avg_volume", volume)
            
            # 거래량 비율
            volume_ratio = volume / avg_volume if avg_volume > 0 else 1
            
            # 스프레드 추정 (시가총액 기반)
            market_cap = price_data.get("market_cap", "1B")
            spread_estimate = self._estimate_spread(market_cap)
            
            # 유동성 리스크 점수
            liquidity_risk_score = min(100, (
                max(0, 1 - volume_ratio) * 50 +  # 거래량 감소
                spread_estimate * 1000  # 스프레드
            ))
            
            return {
                "score": round(liquidity_risk_score, 2),
                "volume_ratio": round(volume_ratio, 2),
                "estimated_spread": round(spread_estimate * 100, 2),
                "daily_volume": volume,
                "avg_volume": avg_volume,
                "level": self._get_risk_level(liquidity_risk_score),
                "factors": self._get_liquidity_risk_factors(volume_ratio, spread_estimate)
            }
        except Exception as e:
            logger.error(f"유동성 리스크 분석 오류: {str(e)}")
            return {"score": 30, "level": "low", "factors": []}
    
    def _analyze_special_risks(self, ticker: str, sentiment_data: List) -> Dict:
        """특수 리스크 분석 (오너 리스크, 규제 리스크 등)"""
        try:
            # 티커별 특수 리스크 설정
            special_risk_profiles = {
                "TSLA": {
                    "owner_risk": {"enabled": True, "keywords": ["Elon Musk", "CEO", "머스크", "일론", "twitter", "트위터"], "weight": 0.8},
                    "regulatory_risk": {"enabled": True, "keywords": ["regulation", "규제", "정부", "리콜", "recall", "investigation"], "weight": 0.7},
                    "competition_risk": {"enabled": True, "keywords": ["BYD", "Rivian", "경쟁사", "전기차", "EV competition"], "weight": 0.6}
                },
                "META": {
                    "owner_risk": {"enabled": True, "keywords": ["Zuckerberg", "저커버그", "CEO"], "weight": 0.6},
                    "regulatory_risk": {"enabled": True, "keywords": ["privacy", "개인정보", "antitrust", "독점"], "weight": 0.8},
                    "metaverse_risk": {"enabled": True, "keywords": ["metaverse", "메타버스", "Reality Labs", "VR"], "weight": 0.7}
                }
            }
            
            # 기본 프로필
            default_profile = {
                "management_risk": {"enabled": True, "keywords": ["CEO", "경영진", "사임", "resignation", "scandal"], "weight": 0.5},
                "regulatory_risk": {"enabled": True, "keywords": ["regulation", "규제", "정부", "lawsuit", "소송"], "weight": 0.5}
            }
            
            profile = special_risk_profiles.get(ticker.upper(), default_profile)
            
            # 각 특수 리스크 계산
            risk_scores = {}
            risk_factors = []
            
            for risk_type, config in profile.items():
                if not config.get("enabled", False):
                    continue
                    
                keywords = config.get("keywords", [])
                weight = config.get("weight", 0.5)
                
                # 감정 데이터에서 키워드 검색
                keyword_count = 0
                negative_keyword_count = 0
                
                for item in sentiment_data:
                    text = (item.get("text", "") + " " + item.get("title", "") + " " + item.get("content", "")).lower()
                    score = item.get("score", 0)
                    # None 값 처리
                    if score is None:
                        score = 0
                    
                    for keyword in keywords:
                        if keyword.lower() in text:
                            keyword_count += 1
                            if score < 0:
                                negative_keyword_count += 1
                
                # 리스크 점수 계산
                if keyword_count > 0:
                    risk_ratio = negative_keyword_count / keyword_count
                    risk_score = min(100, risk_ratio * 100 * weight)
                    
                    risk_scores[risk_type] = risk_score
                    
                    if risk_score > 50:
                        risk_factors.append(f"{risk_type.replace('_', ' ').title()} 감지 ({keyword_count}건 중 {negative_keyword_count}건 부정적)")
            
            # 특수 리스크 종합 점수
            if risk_scores:
                special_risk_score = np.mean(list(risk_scores.values()))
            else:
                special_risk_score = 0
            
            return {
                "score": round(special_risk_score, 2),
                "risk_types": risk_scores,
                "factors": risk_factors,
                "level": self._get_risk_level(special_risk_score)
            }
            
        except Exception as e:
            logger.error(f"특수 리스크 분석 오류: {str(e)}")
            return {"score": 0, "risk_types": {}, "factors": [], "level": "low"}
    
    def _calculate_overall_risk_with_special(
        self, market: Dict, company: Dict, sentiment: Dict, liquidity: Dict, special: Dict
    ) -> tuple:
        """종합 리스크 점수 계산 (특수 리스크 포함)"""
        # 설정된 가중치 사용
        weights = self.risk_weights
        
        # 가중 평균 계산
        overall_score = (
            market.get("score", 50) * weights["market"] +
            company.get("score", 50) * weights["company"] +
            sentiment.get("score", 50) * weights["sentiment"] +
            liquidity.get("score", 30) * weights["liquidity"] +
            special.get("score", 0) * weights["special"]
        )
        
        # 리스크 수준 결정
        risk_level = self._get_risk_level(overall_score)
        
        return round(overall_score, 2), risk_level
    
    def _calculate_overall_risk(
        self, market: Dict, company: Dict, sentiment: Dict, liquidity: Dict
    ) -> tuple:
        """종합 리스크 점수 계산 (레거시)"""
        # 가중치
        weights = {
            "market": 0.3,
            "company": 0.3,
            "sentiment": 0.25,
            "liquidity": 0.15
        }
        
        # 가중 평균 계산
        overall_score = (
            market.get("score", 50) * weights["market"] +
            company.get("score", 50) * weights["company"] +
            sentiment.get("score", 50) * weights["sentiment"] +
            liquidity.get("score", 30) * weights["liquidity"]
        )
        
        # 리스크 수준 결정
        risk_level = self._get_risk_level(overall_score)
        
        return round(overall_score, 2), risk_level
    
    def _generate_risk_recommendations_enhanced(
        self, overall_score: float, market: Dict, company: Dict, 
        sentiment: Dict, liquidity: Dict, special: Dict
    ) -> List[Dict]:
        """향상된 리스크 완화 권고사항 생성"""
        recommendations = []
        
        # 전체 리스크 수준에 따른 기본 권고
        if overall_score > 70:
            recommendations.append({
                "type": "general",
                "priority": "high",
                "action": "포지션 축소 검토",
                "reason": "전반적인 리스크 수준이 높음"
            })
        
        # 특수 리스크 권고 (최우선)
        if special.get("score", 0) > 0:
            for risk_type, score in special.get("risk_types", {}).items():
                if score > 60:
                    risk_name = risk_type.replace("_", " ").title()
                    if "owner" in risk_type:
                        recommendations.append({
                            "type": "special",
                            "priority": "high",
                            "action": "경영진 리스크 모니터링",
                            "reason": f"{risk_name} 높음 - CEO/오너의 행동이 주가에 큰 영향"
                        })
                    elif "regulatory" in risk_type:
                        recommendations.append({
                            "type": "special", 
                            "priority": "high",
                            "action": "규제 동향 주시",
                            "reason": f"{risk_name} 높음 - 규제 변화가 사업에 영향 가능"
                        })
                    elif "competition" in risk_type:
                        recommendations.append({
                            "type": "special",
                            "priority": "medium",
                            "action": "경쟁사 동향 분석",
                            "reason": f"{risk_name} 높음 - 시장 점유율 변화 주의"
                        })
        
        # 시장 리스크 권고
        if market.get("score", 0) > 60:
            recommendations.append({
                "type": "market",
                "priority": "high",
                "action": "헤지 전략 수립",
                "reason": f"높은 베타({market.get('beta', 0)})와 시장 민감도"
            })
        
        # 기업 리스크 권고
        if company.get("score", 0) > 60:
            recommendations.append({
                "type": "company",
                "priority": "medium",
                "action": "분산 투자 강화",
                "reason": f"높은 변동성({company.get('volatility', 0)}%)과 최대낙폭"
            })
        
        # 감성 리스크 권고
        if sentiment.get("score", 0) > 60:
            recommendations.append({
                "type": "sentiment",
                "priority": "medium",
                "action": "단기 모니터링 강화",
                "reason": "부정적 여론 증가 및 의견 분산"
            })
        
        # 유동성 리스크 권고
        if liquidity.get("score", 0) > 50:
            recommendations.append({
                "type": "liquidity",
                "priority": "low",
                "action": "지정가 주문 활용",
                "reason": "낮은 유동성으로 인한 슬리피지 위험"
            })
        
        # 권고사항이 없으면 기본 권고 추가
        if not recommendations:
            recommendations.append({
                "type": "general",
                "priority": "low",
                "action": "현재 포지션 유지",
                "reason": "전반적인 리스크 수준이 관리 가능한 범위"
            })
        
        # 우선순위별 정렬
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 3))
        
        return recommendations
    
    def _generate_risk_recommendations(
        self, overall_score: float, market: Dict, company: Dict, 
        sentiment: Dict, liquidity: Dict
    ) -> List[Dict]:
        """리스크 완화 권고사항 생성 (레거시)"""
        recommendations = []
        
        # 전체 리스크 수준에 따른 기본 권고
        if overall_score > 70:
            recommendations.append({
                "type": "general",
                "priority": "high",
                "action": "포지션 축소 검토",
                "reason": "전반적인 리스크 수준이 높음"
            })
        
        # 시장 리스크 권고
        if market.get("score", 0) > 60:
            recommendations.append({
                "type": "market",
                "priority": "high",
                "action": "헤지 전략 수립",
                "reason": f"높은 베타({market.get('beta', 0)})와 시장 민감도"
            })
        
        # 기업 리스크 권고
        if company.get("score", 0) > 60:
            recommendations.append({
                "type": "company",
                "priority": "medium",
                "action": "분산 투자 강화",
                "reason": f"높은 변동성({company.get('volatility', 0)}%)과 최대낙폭"
            })
        
        # 감성 리스크 권고
        if sentiment.get("score", 0) > 60:
            recommendations.append({
                "type": "sentiment",
                "priority": "medium",
                "action": "단기 모니터링 강화",
                "reason": "부정적 여론 증가 및 의견 분산"
            })
        
        # 유동성 리스크 권고
        if liquidity.get("score", 0) > 50:
            recommendations.append({
                "type": "liquidity",
                "priority": "low",
                "action": "지정가 주문 활용",
                "reason": "낮은 유동성으로 인한 슬리피지 위험"
            })
        
        # 권고사항이 없으면 기본 권고 추가
        if not recommendations:
            recommendations.append({
                "type": "general",
                "priority": "low",
                "action": "현재 포지션 유지",
                "reason": "전반적인 리스크 수준이 관리 가능한 범위"
            })
        
        return recommendations
    
    # 보조 메서드들
    def _calculate_vix_sensitivity(self, beta: float, correlation: float) -> float:
        """VIX 민감도 계산"""
        return min(1.0, beta * correlation * 0.8)
    
    def _calculate_sentiment_variance(self, sentiment_data: List) -> float:
        """감성 분산도 계산"""
        if not sentiment_data:
            return 0.5
        scores = [item.get("score", 0) for item in sentiment_data if "score" in item]
        return np.std(scores) if len(scores) > 1 else 0.5
    
    def _calculate_negative_sentiment_ratio(self, sentiment_data: List) -> float:
        """부정적 감성 비율 계산"""
        if not sentiment_data:
            return 0.3
        scores = [item.get("score", 0) for item in sentiment_data if "score" in item]
        return sum(1 for s in scores if s < 0) / len(scores) if scores else 0.3
    
    def _calculate_source_disagreement(self, sentiment_data: List) -> float:
        """소스별 불일치도 계산"""
        source_scores = {}
        for item in sentiment_data:
            source = item.get("source", "unknown")
            score = item.get("score", 0)
            if source not in source_scores:
                source_scores[source] = []
            source_scores[source].append(score)
        
        if len(source_scores) < 2:
            return 0
        
        source_means = [np.mean(scores) for scores in source_scores.values()]
        return np.std(source_means) if len(source_means) > 1 else 0
    
    def _estimate_spread(self, market_cap_str: str) -> float:
        """시가총액 기반 스프레드 추정"""
        # 시가총액 파싱
        if isinstance(market_cap_str, str):
            if "T" in market_cap_str:
                market_cap = float(market_cap_str.replace("T", "")) * 1e12
            elif "B" in market_cap_str:
                market_cap = float(market_cap_str.replace("B", "")) * 1e9
            elif "M" in market_cap_str:
                market_cap = float(market_cap_str.replace("M", "")) * 1e6
            else:
                market_cap = 1e9  # 기본값
        else:
            market_cap = float(market_cap_str) if market_cap_str else 1e9
        
        # 시가총액 기반 스프레드 추정
        if market_cap > 1e12:  # 1조 이상
            return 0.0001  # 0.01%
        elif market_cap > 1e11:  # 1000억 이상
            return 0.0005  # 0.05%
        elif market_cap > 1e10:  # 100억 이상
            return 0.001   # 0.1%
        else:
            return 0.005   # 0.5%
    
    def _get_risk_level(self, score: float) -> str:
        """리스크 점수에 따른 수준 결정"""
        if score >= 80:
            return "very_high"
        elif score >= 60:
            return "high"
        elif score >= 40:
            return "medium"
        elif score >= 20:
            return "low"
        else:
            return "very_low"
    
    def _get_market_risk_factors(self, beta: float, correlation: float, volatility: float) -> List[str]:
        """시장 리스크 요인 생성"""
        factors = []
        if beta > 1.5:
            factors.append("높은 시장 베타")
        if correlation > 0.8:
            factors.append("시장과 높은 상관관계")
        if volatility > 0.3:
            factors.append("섹터 변동성 상승")
        return factors
    
    def _get_company_risk_factors(
        self, volatility: float, drawdown: float, variance: float, negative: float
    ) -> List[str]:
        """기업 리스크 요인 생성"""
        factors = []
        if volatility > 0.4:
            factors.append("높은 가격 변동성")
        if drawdown > 0.3:
            factors.append("큰 최대 낙폭")
        if variance > 0.5:
            factors.append("의견 불일치 심화")
        if negative > 0.5:
            factors.append("부정적 여론 다수")
        return factors
    
    def _get_sentiment_risk_factors(
        self, avg_sentiment: float, std: float, extreme_negative: float
    ) -> List[str]:
        """감성 리스크 요인 생성"""
        factors = []
        if avg_sentiment < -0.3:
            factors.append("전반적 부정적 감성")
        if std > 0.5:
            factors.append("감성 의견 분산")
        if extreme_negative > 0.3:
            factors.append("극단적 부정 의견 다수")
        return factors
    
    def _get_liquidity_risk_factors(self, volume_ratio: float, spread: float) -> List[str]:
        """유동성 리스크 요인 생성"""
        factors = []
        if volume_ratio < 0.5:
            factors.append("거래량 급감")
        if spread > 0.001:
            factors.append("높은 매수-매도 스프레드")
        return factors
    
    def _get_default_risk_analysis(self) -> Dict:
        """기본 리스크 분석 결과"""
        return {
            "market_risk": {"score": 50, "level": "medium", "factors": []},
            "company_specific_risk": {"score": 50, "level": "medium", "factors": []},
            "sentiment_risk": {"score": 50, "level": "medium", "factors": []},
            "liquidity_risk": {"score": 30, "level": "low", "factors": []},
            "overall_risk_score": 45,
            "risk_level": "medium",
            "recommendations": [{
                "type": "general",
                "priority": "low",
                "action": "추가 데이터 수집 필요",
                "reason": "충분한 데이터가 없어 정확한 분석 불가"
            }]
        }
    
    async def _broadcast_risk_analysis_complete(self, ticker: str, result: Dict):
        """리스크 분석 완료 이벤트 브로드캐스트"""
        event_data = {
            "ticker": ticker,
            "overall_risk_score": result.get("overall_risk_score"),
            "risk_level": result.get("risk_level"),
            "top_risks": self._get_top_risks(result),
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_event("risk_analysis_complete", event_data)
        logger.info(f"📢 리스크 분석 완료 이벤트 브로드캐스트: {ticker}")
    
    def _get_top_risks(self, result: Dict) -> List[str]:
        """상위 리스크 요인 추출"""
        risks = []
        
        risk_types = [
            ("market_risk", "시장"),
            ("company_specific_risk", "기업"),
            ("sentiment_risk", "감성"),
            ("liquidity_risk", "유동성")
        ]
        
        for risk_key, risk_name in risk_types:
            risk_data = result.get(risk_key, {})
            if risk_data.get("score", 0) > 60:
                risks.append(f"{risk_name} 리스크 ({risk_data.get('score', 0)}점)")
        
        return risks[:3]  # 상위 3개만 반환
    
    async def on_start(self):
        """에이전트 시작 시 실행"""
        logger.info("✅ Risk Analysis Agent V2 초기화 완료")
    
    async def on_stop(self):
        """에이전트 종료 시 실행"""
        logger.info("👋 Risk Analysis Agent V2 종료 중...")


# 에이전트 인스턴스 생성
agent = RiskAnalysisAgentV2()

# BaseAgent의 app을 사용
app = agent.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8212)