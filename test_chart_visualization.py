#!/usr/bin/env python3
"""
차트 시각화 기능 테스트 스크립트
"""

import asyncio
import json
import websockets
import time

async def test_charts():
    """차트 기능 테스트"""
    print("🚀 차트 시각화 테스트 시작...")
    print("\n1. 브라우저에서 http://localhost:8100 접속")
    print("2. 종목 분석 요청 (예: '애플 주가 어때?')")
    print("3. 오른쪽 차트 영역에서 실시간 업데이트 확인")
    print("\n차트 확인 사항:")
    print("- 📊 종합 탭: 주요 지표 카드와 감성 분석 파이 차트")
    print("- 📈 주가 탭: 30일 주가 추이 라인 차트")
    print("- 📊 감성분석 탭: 소스별 감성 점수 막대 차트")
    print("- 📉 기술지표 탭: RSI 차트")
    
    # WebSocket 연결 테스트
    try:
        async with websockets.connect('ws://localhost:8100/ws') as websocket:
            print("\n✅ WebSocket 연결 성공!")
            
            # 테스트 메시지 전송
            test_query = "테슬라 주가 분석해줘"
            await websocket.send(json.dumps({
                "type": "analyze",
                "query": test_query
            }))
            print(f"\n📤 테스트 쿼리 전송: '{test_query}'")
            
            # 응답 수신 (10초 동안)
            print("\n📥 차트 업데이트 메시지 수신 중...")
            start_time = time.time()
            chart_updates = []
            
            while time.time() - start_time < 10:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    
                    if data.get('type') == 'chart_update':
                        chart_type = data['payload']['chart_type']
                        chart_updates.append(chart_type)
                        print(f"  - {chart_type} 차트 업데이트 수신")
                        
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"에러: {e}")
                    break
            
            print(f"\n📊 수신된 차트 업데이트 종류: {list(set(chart_updates))}")
            
    except Exception as e:
        print(f"\n❌ WebSocket 연결 실패: {e}")
        print("서버가 실행 중인지 확인하세요.")

def check_html_features():
    """HTML 파일의 차트 기능 확인"""
    print("\n📄 HTML 차트 기능 확인:")
    
    features = {
        "Chart.js 라이브러리": "cdn.jsdelivr.net/npm/chart.js",
        "2열 레이아웃": "grid-template-columns: 1fr 1fr",
        "차트 탭 인터페이스": "chart-tabs",
        "감성 분석 파이 차트": "sentimentPieChart",
        "주가 라인 차트": "priceChart",
        "감성 점수 막대 차트": "sentimentBarChart",
        "RSI 차트": "rsiChart",
        "실시간 WebSocket": "ws://localhost:8100/ws"
    }
    
    try:
        with open("index_v2.html", "r", encoding="utf-8") as f:
            html_content = f.read()
            
        for feature, keyword in features.items():
            if keyword in html_content:
                print(f"  ✅ {feature}")
            else:
                print(f"  ❌ {feature}")
                
    except FileNotFoundError:
        print("  ❌ index_v2.html 파일을 찾을 수 없습니다.")

def main():
    """메인 함수"""
    print("=" * 60)
    print("A2A 감성 분석 시스템 - 차트 시각화 기능 테스트")
    print("=" * 60)
    
    # HTML 기능 확인
    check_html_features()
    
    # WebSocket 테스트
    print("\n🔄 WebSocket 차트 업데이트 테스트 중...")
    asyncio.run(test_charts())
    
    print("\n" + "=" * 60)
    print("테스트 완료! 브라우저에서 차트를 확인하세요.")
    print("=" * 60)

if __name__ == "__main__":
    main()