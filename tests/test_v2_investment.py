#!/usr/bin/env python3
"""
V2 시스템으로 실제 투자 분석 테스트
"""

import asyncio
import json
import websockets
from datetime import datetime

async def test_investment_analysis():
    """투자 분석 테스트"""
    uri = "ws://localhost:8100/ws/v2"
    
    queries = [
        "애플 주가 어때?",
        "테슬라 투자해도 될까?",
        "NVDA 분석해줘"
    ]
    
    for query in queries:
        print(f"\n{'='*60}")
        print(f"🔍 분석 요청: {query}")
        print(f"{'='*60}")
        
        try:
            async with websockets.connect(uri) as websocket:
                # 분석 요청 전송
                message = {
                    "query": query,
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send(json.dumps(message))
                print("✅ 요청 전송 완료")
                
                # 응답 수신
                print("\n📊 분석 진행 상황:")
                while True:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=60.0)
                        data = json.loads(response)
                        
                        # 상태 업데이트
                        if data.get("type") == "status":
                            print(f"  ▶ {data.get('message', 'Processing...')}")
                        
                        # 에러 처리
                        elif data.get("type") == "error":
                            print(f"  ❌ 에러: {data.get('message', 'Unknown error')}")
                            break
                        
                        # 최종 결과
                        elif data.get("type") == "result":
                            print("\n✅ 분석 완료!")
                            result = data.get("data", {})
                            
                            # 티커 정보
                            if "ticker" in result:
                                print(f"\n📈 종목: {result['ticker']}")
                            
                            # 정량적 분석 결과
                            if "quantitative_analysis" in result:
                                print("\n📊 정량적 분석:")
                                quant = result["quantitative_analysis"]
                                if "current_price" in quant:
                                    print(f"  - 현재가: ${quant['current_price']}")
                                if "technical_indicators" in quant:
                                    tech = quant["technical_indicators"]
                                    print(f"  - RSI: {tech.get('rsi', 'N/A')}")
                                    print(f"  - MACD: {tech.get('macd', 'N/A')}")
                            
                            # 감성 분석 결과
                            if "sentiment_analysis" in result:
                                print("\n💭 감성 분석:")
                                sent = result["sentiment_analysis"]
                                if "overall_sentiment" in sent:
                                    print(f"  - 전반적 감성: {sent['overall_sentiment']}")
                                if "confidence" in sent:
                                    print(f"  - 신뢰도: {sent['confidence']:.2%}")
                            
                            # 리스크 분석 결과
                            if "risk_analysis" in result:
                                print("\n⚠️ 리스크 분석:")
                                risk = result["risk_analysis"]
                                if "overall_risk" in risk:
                                    print(f"  - 전반적 리스크: {risk['overall_risk']}")
                                if "risk_factors" in risk:
                                    print(f"  - 주요 리스크: {', '.join(risk['risk_factors'][:3])}")
                            
                            # 최종 점수
                            if "weighted_score" in result:
                                print(f"\n🎯 종합 점수: {result['weighted_score']:.2f}/100")
                            
                            # 최종 보고서
                            if "report" in result:
                                print("\n📝 투자 분석 보고서:")
                                print(result["report"][:500] + "..." if len(result["report"]) > 500 else result["report"])
                            
                            break
                        
                        # 기타 메시지
                        else:
                            print(f"  ℹ️ {data}")
                            
                    except asyncio.TimeoutError:
                        print("  ⏱️ 타임아웃 - 분석에 시간이 오래 걸리고 있습니다...")
                        break
                        
        except Exception as e:
            print(f"❌ 연결 실패: {str(e)}")
        
        # 다음 분석 전 잠시 대기
        await asyncio.sleep(2)
    
    print(f"\n{'='*60}")
    print("✅ 모든 테스트 완료!")
    print(f"{'='*60}")

if __name__ == "__main__":
    print("🚀 V2 투자 분석 시스템 테스트 시작...")
    asyncio.run(test_investment_analysis())