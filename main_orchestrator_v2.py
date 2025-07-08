"""
Main Orchestrator V2 - A2A 프로토콜 기반

에이전트 간 직접 통신을 지원하는 새로운 오케스트레이터
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List

from a2a_core.base.base_agent import BaseAgent
from a2a_core.protocols.message import A2AMessage, MessageType, Priority


class OrchestratorV2(BaseAgent):
    """A2A 오케스트레이터 V2"""
    
    def __init__(self):
        super().__init__(
            name="Orchestrator V2",
            description="A2A 기반 투자 분석 시스템 오케스트레이터",
            port=8100,  # 새로운 포트
            registry_url="http://localhost:8001"
        )
        
        # WebSocket 연결 관리
        self.active_websockets: List[WebSocket] = []
        
        # 분석 세션 관리
        self.analysis_sessions: Dict[str, Dict] = {}
        
        # CORS 설정
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 웹 라우트 추가
        self._setup_web_routes()
        
    def _setup_web_routes(self):
        """웹 인터페이스 라우트 설정"""
        
        @self.app.get("/")
        async def read_index():
            return FileResponse("index_v2.html")
            
        @self.app.get("/agents.json")
        async def get_agents():
            return FileResponse("agents.json")
            
        @self.app.websocket("/ws/v2")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.active_websockets.append(websocket)
            print(f"🔌 WebSocket 연결 수락됨. 활성 연결 수: {len(self.active_websockets)}")
            
            try:
                # 초기 데이터 수신
                print("⏳ WebSocket에서 초기 데이터 대기 중...")
                init_data = await websocket.receive_json()
                print(f"📥 수신된 데이터: {init_data}")
                user_query = init_data.get("query")
                
                if not user_query:
                    print("❌ 쿼리가 비어있습니다")
                    await websocket.send_json({"type": "error", "payload": {"message": "쿼리가 필요합니다"}})
                    return
                
                # 분석 세션 시작
                print(f"🚀 분석 세션 시작 중: {user_query}")
                session_id = await self.start_analysis_session(user_query, websocket)
                print(f"📋 세션 ID: {session_id}")
                
                # 연결 유지
                while True:
                    await asyncio.sleep(1)
                    
            except WebSocketDisconnect:
                self.active_websockets.remove(websocket)
                print(f"🔌 WebSocket 연결 종료. 남은 연결 수: {len(self.active_websockets)}")
            except Exception as e:
                print(f"❌ WebSocket 오류: {e}")
                import traceback
                traceback.print_exc()
                
    async def on_start(self):
        """오케스트레이터 시작"""
        # 능력 등록
        await self.register_capability({
            "name": "orchestrate_analysis",
            "version": "2.0",
            "description": "투자 분석 워크플로우 조율",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "사용자 질문"}
                },
                "required": ["query"]
            }
        })
        
        print("✅ Orchestrator V2 초기화 완료")
        
    async def on_stop(self):
        """오케스트레이터 종료"""
        # 모든 WebSocket 연결 종료
        for ws in self.active_websockets:
            await ws.close()
            
        print("🛑 Orchestrator V2 종료")
        
    async def handle_message(self, message: A2AMessage):
        """메시지 처리"""
        try:
            print(f"\n{'*'*70}")
            print(f"📩 메시지 수신:")
            print(f"   - Type: {message.header.message_type}")
            print(f"   - From: {message.header.sender_id}")
            print(f"   - Message ID: {message.header.message_id}")
            print(f"   - Correlation ID: {message.header.correlation_id}")
            print(f"   - Body keys: {list(message.body.keys()) if message.body else 'None'}")
            print(f"{'*'*70}\n")
            
            if message.header.message_type == MessageType.RESPONSE:
                # 응답 메시지 처리
                correlation_id = message.header.correlation_id
                print(f"🔄 응답 메시지 처리 중. Correlation ID: {correlation_id}")
                
                # 모든 세션 확인
                print(f"📋 현재 활성 세션 수: {len(self.analysis_sessions)}")
                for sid, session in self.analysis_sessions.items():
                    print(f"   - Session {sid}: state={session.get('state')}, nlu_request_id={session.get('nlu_request_id')}")
                
                # correlation_id로 세션 찾기
                session_found = False
                for session_id, session in self.analysis_sessions.items():
                    # NLU 요청 확인
                    if session.get("nlu_request_id") == correlation_id:
                        print(f"✅ NLU 응답 - 세션 발견: {session_id}")
                        await self._handle_agent_response(session, message)
                        session_found = True
                        break
                    # 데이터 수집 요청 확인 - 각 요청 ID 출력
                    data_request_ids = session.get("data_request_ids", {})
                    if data_request_ids:
                        print(f"   📋 세션 {session_id}의 데이터 수집 요청 ID:")
                        for agent_type, req_id in data_request_ids.items():
                            print(f"      - {agent_type}: {req_id} {'✓' if req_id == correlation_id else ''}")
                            if req_id == correlation_id:
                                print(f"\n✅ 매치 발견!")
                                print(f"   - Agent type: {agent_type}")
                                print(f"   - Session ID: {session_id}")
                                print(f"   - Request ID: {req_id}")
                                print(f"   - Correlation ID: {correlation_id}")
                                await self._handle_agent_response(session, message)
                                session_found = True
                                break
                    if session_found:
                        break
                    # 감정 분석 요청 확인
                    elif session.get("sentiment_request_id") == correlation_id:
                        print(f"✅ 감정 분석 응답 - 세션 발견: {session_id}")
                        await self._handle_agent_response(session, message)
                        session_found = True
                        break
                    # 정량적 분석 요청 확인
                    elif session.get("quantitative_request_id") == correlation_id:
                        print(f"✅ 정량적 분석 응답 - 세션 발견: {session_id}")
                        await self._handle_agent_response(session, message)
                        session_found = True
                        break
                    # 점수 계산 요청 확인
                    elif session.get("score_request_id") == correlation_id:
                        print(f"✅ 점수 계산 응답 - 세션 발견: {session_id}")
                        await self._handle_agent_response(session, message)
                        session_found = True
                        break
                    # 리스크 분석 요청 확인
                    elif session.get("risk_request_id") == correlation_id:
                        print(f"✅ 리스크 분석 응답 - 세션 발견: {session_id}")
                        await self._handle_agent_response(session, message)
                        session_found = True
                        break
                    # 리포트 생성 요청 확인
                    elif session.get("report_request_id") == correlation_id:
                        print(f"✅ 리포트 생성 응답 - 세션 발견: {session_id}")
                        await self._handle_agent_response(session, message)
                        session_found = True
                        break
                        
                if not session_found:
                    print(f"⚠️ Correlation ID {correlation_id}에 해당하는 세션을 찾을 수 없음")
                    
            elif message.header.message_type == MessageType.EVENT:
                # 이벤트 처리
                event_type = message.body.get("event_type")
                print(f"📢 이벤트 수신: {event_type}")
                await self._handle_event(event_type, message)
                
        except Exception as e:
            print(f"❌ 메시지 처리 오류: {e}")
            import traceback
            traceback.print_exc()
            
    async def start_analysis_session(self, query: str, websocket: WebSocket) -> str:
        """분석 세션 시작"""
        import uuid
        session_id = str(uuid.uuid4())
        print(f"📝 새 세션 생성: {session_id}")
        
        # 세션 정보 저장
        self.analysis_sessions[session_id] = {
            "query": query,
            "websocket": websocket,
            "state": "started",
            "results": {}
        }
        print(f"💾 세션 정보 저장 완료")
        
        # UI 상태 업데이트
        print("📤 UI에 상태 업데이트 전송 중...")
        await self._send_to_ui(websocket, "status", {"agentId": "orchestrator"})
        await self._send_to_ui(websocket, "log", {"message": f"🚀 A2A 분석 시작: {query}"})
        
        # Step 1: NLU 에이전트 직접 호출 (하드코딩)
        print("🔎 NLU 에이전트 호출 중...")
        
        # 레지스트리 없이 직접 호출
        try:
            async with httpx.AsyncClient() as client:
                print("📤 NLU 에이전트에 직접 HTTP 요청...")
                response = await client.post(
                    "http://localhost:8108/extract_ticker",
                    json={"query": query},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    nlu_result = response.json()
                    print(f"✅ NLU 응답 받음: {nlu_result}")
                    
                    # 세션에 결과 저장
                    self.analysis_sessions[session_id]["ticker"] = nlu_result.get("ticker", "")
                    self.analysis_sessions[session_id]["company_name"] = nlu_result.get("company_name", "")
                    
                    await self._send_to_ui(websocket, "log", {
                        "message": f"✅ 티커 추출 완료: {nlu_result.get('ticker', 'N/A')}"
                    })
                    
                    # 다음 단계로 진행
                    session = self.analysis_sessions[session_id]
                    session["state"] = "collecting_data"
                    await self._start_data_collection(session)
                    
                else:
                    print(f"❌ NLU 에이전트 오류: HTTP {response.status_code}")
                    await self._send_to_ui(websocket, "log", {"message": "❌ NLU 에이전트 오류"})
                    
        except Exception as e:
            print(f"❌ NLU 에이전트 연결 실패: {e}")
            await self._send_to_ui(websocket, "log", {"message": f"❌ NLU 에이전트 연결 실패: {str(e)}"})
            
        return session_id
        
    async def _handle_agent_response(self, session: Dict, message: A2AMessage):
        """에이전트 응답 처리"""
        websocket = session["websocket"]
        state = session["state"]
        
        print(f"\n{'='*60}")
        print(f"🔄 에이전트 응답 처리 시작")
        print(f"   - Session state: {state}")
        print(f"   - Sender ID: {message.header.sender_id}")
        print(f"   - Message ID: {message.header.message_id}")
        print(f"   - Correlation ID: {message.header.correlation_id}")
        print(f"   - Message body keys: {list(message.body.keys()) if message.body else 'None'}")
        print(f"{'='*60}\n")
        
        if state == "waiting_nlu":
            # NLU 응답 처리
            result = message.body.get("result", {})
            ticker = result.get("ticker")
            
            print(f"📊 NLU 결과:")
            print(f"   - Ticker: {ticker}")
            print(f"   - Full result: {result}")
            
            await self._send_to_ui(websocket, "log", {"message": result.get("log_message", "")})
            
            if ticker:
                session["ticker"] = ticker
                session["state"] = "collecting_data"
                print(f"✅ 티커 찾음: {ticker}, 데이터 수집 시작")
                
                # 데이터 수집 에이전트들 찾기
                await self._start_data_collection(session)
            else:
                print("❌ 티커를 찾을 수 없음")
                await self._send_to_ui(websocket, "log", {"message": "❌ 티커를 찾을 수 없습니다"})
                
        elif state == "collecting_data":
            # 데이터 수집 응답 처리
            sender_id = message.header.sender_id
            correlation_id = message.header.correlation_id
            result = message.body.get("result", {})
            
            print(f"\n📊 데이터 수집 응답 처리")
            print(f"   - Sender ID: {sender_id}")
            print(f"   - Correlation ID: {correlation_id}")
            print(f"   - Result keys: {list(result.keys())}")
            print(f"   - Result status: {result.get('status', 'N/A')}")
            
            # 현재 세션의 요청 ID 목록 출력
            print(f"\n📋 현재 세션의 데이터 수집 요청 ID:")
            for atype, req_id in session.get("data_request_ids", {}).items():
                print(f"   - {atype}: {req_id}")
            
            # 어떤 에이전트의 응답인지 확인
            agent_type = None
            for atype, req_id in session.get("data_request_ids", {}).items():
                if req_id == correlation_id:
                    agent_type = atype
                    break
                    
            if not agent_type:
                print(f"\n⚠️ 알 수 없는 데이터 수집 응답: {correlation_id}")
                print(f"   세션에 등록된 요청 ID와 일치하지 않습니다.")
                return
                
            print(f"\n✅ {agent_type} 에이전트 응답 확인")
            
            # 결과 저장
            if "collected_data" not in session:
                session["collected_data"] = {}
                print(f"   📂 collected_data 초기화")
                
            # 에이전트 타입별로 데이터 저장
            data = result.get("data", [])
            session["collected_data"][agent_type] = data
            
            # 로그 출력
            data_count = len(data)
            print(f"   - 수집된 데이터: {data_count}개")
            if data:
                print(f"   - 첫 번째 데이터 항목 키: {list(data[0].keys()) if isinstance(data[0], dict) else 'Not a dict'}")
                print(f"   - 데이터 샘플 (첫 50자): {str(data[0])[:50]}...")
            else:
                print(f"   - 데이터가 비어있음")
            
            await self._send_to_ui(websocket, "log", {
                "message": f"✅ {agent_type.upper()} 데이터 수집 완료: {data_count}개 항목"
            })
            
            # 각 데이터 항목의 로그 메시지 출력
            for item in result.get("data", []):
                if "log_message" in item:
                    await self._send_to_ui(websocket, "log", {"message": item["log_message"]})
                    
            # 응답받은 에이전트를 대기 목록에서 제거
            pending_agents = session.get("pending_data_agents", [])
            print(f"\n🔄 대기 중인 에이전트 업데이트")
            print(f"   - 현재 대기 목록: {pending_agents}")
            
            if agent_type in pending_agents:
                session["pending_data_agents"].remove(agent_type)
                print(f"   - {agent_type} 제거 완료")
                print(f"   - 남은 대기 에이전트: {session['pending_data_agents']}")
            else:
                print(f"   ⚠️ {agent_type}가 대기 목록에 없음 (이미 처리됨?)")
                
            # 모든 데이터 수집 완료 확인
            remaining_agents = session.get("pending_data_agents", [])
            collected_data = session.get("collected_data", {})
            print(f"\n📊 데이터 수집 상태 확인")
            print(f"   - 남은 에이전트 수: {len(remaining_agents)}")
            print(f"   - 수집된 데이터 소스: {list(collected_data.keys())}")
            
            # 모든 데이터 수집이 완료되면 진행 (대기 목록이 비어있으면)
            if len(remaining_agents) == 0 and not session.get("sentiment_started", False):
                print("\n🎉 모든 데이터 수집 완료!")
                await self._send_to_ui(websocket, "log", {"message": "🎉 모든 데이터 수집 완료!"})
                
                # 수집된 데이터 요약
                total_items = 0
                for source, items in session.get("collected_data", {}).items():
                    count = len(items)
                    total_items += count
                    print(f"   - {source}: {count}개 항목")
                print(f"   - 총 {total_items}개 항목 수집됨")
                
                # 다음 단계로 진행 (감정 분석)
                print(f"\n➡️ 다음 단계로 진행: 감정 분석")
                session["state"] = "analyzing_sentiment"
                session["sentiment_started"] = True  # 중복 실행 방지
                await self._start_sentiment_analysis(session)
            else:
                print(f"\n⏳ 아직 {len(remaining_agents)}개 에이전트 응답 대기 중: {remaining_agents}")
            
        elif state == "analyzing_sentiment":
            # 감정 분석 응답 처리
            print(f"🎯 감정 분석 응답 처리")
            result = message.body.get("result", {})
            
            # 감정 분석 결과 저장 (sentiment agent는 analyzed_results를 반환함)
            analyzed_results = result.get("analyzed_results", [])
            session["sentiment_analysis"] = analyzed_results
            
            # 로그 출력
            success_count = result.get("success_count", 0)
            await self._send_to_ui(websocket, "log", {
                "message": f"✅ 감정 분석 완료: {success_count}개 항목 분석"
            })
            
            # 각 분석 결과의 요약 출력
            for ticker_data in analyzed_results:
                source = ticker_data.get("source", "unknown")
                score = ticker_data.get("score", 0)
                summary = ticker_data.get("summary", "요약 없음")
                
                # 점수를 기반으로 레이블 결정
                if score > 0.3:
                    label = "positive"
                elif score < -0.3:
                    label = "negative"
                else:
                    label = "neutral"
                
                emoji = "🟢" if label == "positive" else "🔴" if label == "negative" else "🟡"
                await self._send_to_ui(websocket, "log", {
                    "message": f"  {emoji} {source}: {label} (점수: {score:.2f})"
                })
            
            # 다음 단계로 진행 (정량적 분석)
            session["state"] = "quantitative_analysis"
            await self._start_quantitative_analysis(session)
            
        elif state == "quantitative_analysis":
            # 정량적 분석 응답 처리
            print(f"📊 정량적 분석 응답 처리")
            result = message.body.get("result", {})
            
            # 정량적 분석 결과 저장
            session["quantitative_analysis"] = result
            
            # 결과 출력
            await self._send_to_ui(websocket, "log", {
                "message": "✅ 정량적 데이터 분석 완료"
            })
            
            # 주요 지표 출력
            price_data = result.get("price_data", {})
            if price_data:
                await self._send_to_ui(websocket, "log", {
                    "message": f"  📈 현재가: ${price_data.get('current', 0):.2f} ({price_data.get('change_1d', 0):+.2f}%)"
                })
            
            technical = result.get("technical_indicators", {})
            if technical:
                await self._send_to_ui(websocket, "log", {
                    "message": f"  📊 RSI: {technical.get('rsi', 50):.1f}, MACD: {technical.get('macd_signal', 'N/A')}"
                })
            
            # 다음 단계로 진행 (리스크 분석)
            session["state"] = "risk_analysis"
            await self._start_risk_analysis(session)
            
        elif state == "calculating_score":
            # 점수 계산 응답 처리
            print(f"📊 점수 계산 응답 처리")
            result = message.body.get("result", {})
            
            # 점수 계산 결과 저장
            session["score_calculation"] = result
            
            # 결과 출력
            final_score = result.get("final_score", 0)
            final_label = result.get("final_label", "neutral")
            weighted_scores = result.get("weighted_scores", {})
            
            emoji = "🟢" if final_label == "positive" else "🔴" if final_label == "negative" else "🟡"
            await self._send_to_ui(websocket, "log", {
                "message": f"✅ 점수 계산 완료"
            })
            await self._send_to_ui(websocket, "log", {
                "message": f"{emoji} 최종 점수: {final_score:.2f} ({final_label})"
            })
            
            # 가중치 적용된 점수 출력
            for source, score_info in weighted_scores.items():
                await self._send_to_ui(websocket, "log", {
                    "message": f"  - {source}: {score_info.get('weighted_score', 0):.2f} (가중치: {score_info.get('weight', 0)})"
                })
            
            # 다음 단계로 진행 (리스크 분석)
            session["state"] = "risk_analysis"
            await self._start_risk_analysis(session)
            
        elif state == "risk_analysis":
            # 리스크 분석 응답 처리
            print(f"🎯 리스크 분석 응답 처리")
            result = message.body.get("result", {})
            
            # 리스크 분석 결과 저장
            session["risk_analysis"] = result
            
            # 결과 출력
            overall_risk_score = result.get("overall_risk_score", 0)
            risk_level = result.get("risk_level", "medium")
            
            risk_emoji = "🟢" if risk_level in ["very_low", "low"] else "🟡" if risk_level == "medium" else "🔴"
            await self._send_to_ui(websocket, "log", {
                "message": f"✅ 리스크 분석 완료"
            })
            await self._send_to_ui(websocket, "log", {
                "message": f"{risk_emoji} 종합 리스크: {overall_risk_score:.1f}점 ({risk_level})"
            })
            
            # 주요 리스크 권고사항
            recommendations = result.get("recommendations", [])
            if recommendations:
                await self._send_to_ui(websocket, "log", {
                    "message": "  💡 주요 권고사항:"
                })
                for rec in recommendations[:3]:  # 상위 3개만
                    await self._send_to_ui(websocket, "log", {
                        "message": f"    - {rec.get('action', '')}: {rec.get('reason', '')}"
                    })
            
            # 다음 단계로 진행 (리포트 생성)
            session["state"] = "generating_report"
            await self._start_report_generation(session)
            
        elif state == "generating_report":
            # 보고서 생성 응답 처리
            print(f"📝 보고서 생성 응답 처리")
            result = message.body.get("result", {})
            
            # 리포트 저장
            session["final_report"] = result.get("report", "")
            
            # UI에 최종 결과 전송
            await self._send_to_ui(websocket, "log", {
                "message": "✅ 분석 보고서 생성 완료!"
            })
            
            # 최종 결과 전송
            await self._send_to_ui(websocket, "result", {
                "ticker": session.get("ticker"),
                "final_score": session.get("score_calculation", {}).get("final_score", 0),
                "final_label": session.get("score_calculation", {}).get("final_label", "neutral"),
                "report": session["final_report"],
                "weighted_scores": session.get("score_calculation", {}).get("weighted_scores", {}),
                "data_summary": {
                    "news": len(session.get("collected_data", {}).get("news", [])),
                    "twitter": len(session.get("collected_data", {}).get("twitter", [])),
                    "sec": len(session.get("collected_data", {}).get("sec", []))
                }
            })
            
            # 분석 완료 상태
            session["state"] = "completed"
            await self._send_to_ui(websocket, "log", {
                "message": "🎉 전체 분석 프로세스 완료!"
            })
        
    async def _start_data_collection(self, session: Dict):
        """데이터 수집 시작"""
        ticker = session["ticker"]
        websocket = session["websocket"]
        session_id = None
        
        # 세션 ID 찾기
        for sid, sess in self.analysis_sessions.items():
            if sess == session:
                session_id = sid
                break
                
        print(f"🔄 데이터 수집 시작")
        print(f"   - Ticker: {ticker}")
        print(f"   - Session ID: {session_id}")
        
        await self._send_to_ui(websocket, "status", {"agentId": "data-collection"})
        await self._send_to_ui(websocket, "log", {"message": "📊 데이터 수집 시작..."})
        
        # 직접 HTTP 호출로 데이터 수집
        print("🔎 데이터 수집 에이전트 직접 호출...")
        
        # 각 에이전트의 포트 정보
        agent_ports = {
            "news": 8307,
            "twitter": 8209,
            "sec": 8210
        }
        
        # 데이터 수집 요청 추적을 위한 딕셔너리
        session["data_request_ids"] = {}
        session["pending_data_agents"] = []
        session["collected_data"] = {}  # 미리 초기화
        
        print(f"\n📝 데이터 수집 추적 정보 초기화")
        print(f"   - data_request_ids: {{}}")
        print(f"   - pending_data_agents: []")
        print(f"   - collected_data: {{}}")
        
        # 병렬로 데이터 수집 요청
        tasks = []
        for agent_type, port in agent_ports.items():
            print(f"\n📤 {agent_type} 에이전트에게 요청 전송 중...")
            print(f"   - Port: {port}")
            print(f"   - Payload: {{'ticker': '{ticker}'}}")
            
            # 비동기 태스크 생성
            task = self._send_data_collection_request_http(
                session_id, 
                agent_type, 
                port, 
                ticker,
                websocket
            )
            tasks.append(task)
            session["pending_data_agents"].append(agent_type)
                
        # 모든 요청 동시 전송
        print(f"\n⏳ {len(tasks)}개의 데이터 수집 요청 동시 전송 중...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 결과 확인
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"❌ 태스크 {i} 실패: {result}")
            else:
                print(f"✅ 태스크 {i} 완료")
                
        print(f"✅ 모든 데이터 수집 요청 전송 완료")
        
    async def _send_data_collection_request_http(self, session_id: str, agent_type: str, 
                                               port: int, ticker: str, websocket: WebSocket):
        """HTTP로 개별 데이터 수집 요청 전송"""
        try:
            print(f"\n{'~'*50}")
            print(f"📤 {agent_type} 데이터 수집 HTTP 요청 시작")
            print(f"   - Session ID: {session_id}")
            print(f"   - Port: {port}")
            print(f"   - Ticker: {ticker}")
            
            # UI 상태 업데이트
            await self._send_to_ui(websocket, "status", {"agentId": f"{agent_type}-agent"})
            await self._send_to_ui(websocket, "log", {
                "message": f"📡 {agent_type.upper()} 데이터 수집 요청 중..."
            })
            
            # HTTP 요청 - 직접 엔드포인트 호출
            async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=30.0)) as client:
                endpoint = f"http://localhost:{port}/collect_{agent_type}_data"
                print(f"   - Endpoint: {endpoint}")
                
                try:
                    response = await client.post(
                        endpoint,
                        json={"ticker": ticker},
                        timeout=60.0
                    )
                except httpx.ConnectError as e:
                    print(f"❌ {agent_type} 연결 실패: {e}")
                    # 재시도 한 번
                    print(f"🔄 {agent_type} 재시도 중...")
                    await asyncio.sleep(1)
                    response = await client.post(
                        endpoint,
                        json={"ticker": ticker},
                        timeout=60.0
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ {agent_type} 요청 성공")
                    print(f"   - Response keys: {list(result.keys())}")
                    
                    # HTTP 직접 응답에서 데이터 추출
                    data = result.get("data", [])
                    print(f"   - Data count: {len(data)}")
                    
                    # 세션에 데이터 저장
                    session = self.analysis_sessions.get(session_id)
                    if session:
                        if "collected_data" not in session:
                            session["collected_data"] = {}
                        session["collected_data"][agent_type] = data
                        
                        # 대기 목록에서 제거
                        if agent_type in session.get("pending_data_agents", []):
                            session["pending_data_agents"].remove(agent_type)
                        
                        # UI 업데이트
                        await self._send_to_ui(websocket, "log", {
                            "message": f"✅ {agent_type.upper()} 데이터 수집 완료: {len(data)}개 항목"
                        })
                        
                        # 모든 데이터 수집 완료 확인
                        if not session.get("pending_data_agents"):
                            print("🎉 모든 데이터 수집 완료!")
                            await self._send_to_ui(websocket, "log", {"message": "🎉 모든 데이터 수집 완료!"})
                            session["state"] = "analyzing_sentiment"
                            await self._start_sentiment_analysis(session)
                    
                    print(f"{'~'*50}\n")
                    return result
                else:
                    print(f"❌ {agent_type} 요청 실패: HTTP {response.status_code}")
                    await self._send_to_ui(websocket, "log", {
                        "message": f"❌ {agent_type.upper()} 데이터 수집 실패"
                    })
                    
        except Exception as e:
            print(f"❌ {agent_type} 요청 중 오류: {e}")
            await self._send_to_ui(websocket, "log", {
                "message": f"❌ {agent_type.upper()} 데이터 수집 오류: {str(e)}"
            })
            import traceback
            traceback.print_exc()
            
        print(f"{'~'*50}\n")
        return None
        
    async def _start_quantitative_analysis(self, session: Dict):
        """정량적 분석 시작"""
        print("📊 정량적 분석 단계 시작")
        websocket = session["websocket"]
        ticker = session["ticker"]
        
        # UI 업데이트
        await self._send_to_ui(websocket, "status", {"agentId": "quantitative-agent"})
        await self._send_to_ui(websocket, "log", {"message": f"📊 {ticker} 기술적 지표 분석 중..."})
        
        try:
            # 정량적 분석 HTTP 호출
            async with httpx.AsyncClient() as client:
                print(f"📤 정량적 분석 HTTP 요청 전송 중...")
                response = await client.post(
                    "http://localhost:8211/quantitative_analysis",
                    json={"ticker": ticker},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ 정량적 분석 응답 받음")
                    
                    # 결과 저장
                    session["quantitative_analysis"] = result.get("analysis", {})
                    
                    # UI 업데이트
                    await self._send_to_ui(websocket, "log", {
                        "message": f"✅ 기술적 지표 분석 완료"
                    })
                    
                    # 다음 단계로 (리스크 분석)
                    session["state"] = "risk_analysis"
                    await self._start_risk_analysis(session)
                    
                else:
                    print(f"❌ 정량적 분석 에이전트 오류: HTTP {response.status_code}")
                    await self._send_to_ui(websocket, "log", {"message": "❌ 정량적 분석 실패"})
                    # 실패해도 다음 단계로 진행
                    session["state"] = "risk_analysis"
                    await self._start_risk_analysis(session)
                    
        except Exception as e:
            print(f"❌ 정량적 분석 요청 중 오류: {e}")
            await self._send_to_ui(websocket, "log", {
                "message": f"❌ 정량적 분석 오류: {str(e)}"
            })
            # 오류가 나도 다음 단계로 진행
            session["state"] = "risk_analysis"
            await self._start_risk_analysis(session)
    
    async def _start_risk_analysis(self, session: Dict):
        """리스크 분석 시작"""
        print("⚠️ 리스크 분석 단계 시작")
        websocket = session["websocket"]
        ticker = session["ticker"]
        
        # UI 업데이트
        await self._send_to_ui(websocket, "status", {"agentId": "risk-agent"})
        await self._send_to_ui(websocket, "log", {"message": f"⚠️ {ticker} 투자 리스크 분석 중..."})
        
        try:
            # 리스크 분석을 위한 데이터 준비
            request_data = {
                "ticker": ticker,
                "quantitative_data": session.get("quantitative_analysis", {}),
                "sentiment_data": session.get("sentiment_analysis", [])
            }
            
            # 리스크 분석 HTTP 호출
            async with httpx.AsyncClient() as client:
                print(f"📤 리스크 분석 HTTP 요청 전송 중...")
                response = await client.post(
                    "http://localhost:8212/risk_analysis",
                    json=request_data,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ 리스크 분석 응답 받음")
                    
                    # 결과 저장
                    session["risk_analysis"] = result.get("risk_analysis", {})
                    
                    # UI 업데이트
                    risk_level = session["risk_analysis"].get("risk_level", "Unknown")
                    overall_score = session["risk_analysis"].get("overall_risk_score", 0)
                    
                    risk_emoji = "🟢" if risk_level == "Low" else "🟡" if risk_level == "Medium" else "🔴"
                    await self._send_to_ui(websocket, "log", {
                        "message": f"✅ 리스크 분석 완료: {risk_emoji} {risk_level} (점수: {overall_score:.2f})"
                    })
                    
                    # 다음 단계로
                    session["state"] = "calculating_score"
                    await self._start_score_calculation(session)
                    
                else:
                    print(f"❌ 리스크 분석 에이전트 오류: HTTP {response.status_code}")
                    await self._send_to_ui(websocket, "log", {"message": "❌ 리스크 분석 실패"})
                    # 실패해도 다음 단계로 진행
                    session["state"] = "calculating_score"
                    await self._start_score_calculation(session)
                    
        except Exception as e:
            print(f"❌ 리스크 분석 요청 중 오류: {e}")
            await self._send_to_ui(websocket, "log", {
                "message": f"❌ 리스크 분석 오류: {str(e)}"
            })
            # 오류가 나도 다음 단계로 진행
            session["state"] = "calculating_score"
            await self._start_score_calculation(session)
    
    async def _start_sentiment_analysis(self, session: Dict):
        """감정 분석 시작"""
        print("🎯 감정 분석 단계 시작")
        websocket = session["websocket"]
        ticker = session["ticker"]
        collected_data = session.get("collected_data", {})
        
        # 세션 ID 찾기
        session_id = None
        for sid, sess in self.analysis_sessions.items():
            if sess == session:
                session_id = sid
                break
                
        # 수집된 모든 데이터를 하나로 합치기
        all_data = []
        for source, data_list in collected_data.items():
            for item in data_list:
                item["source"] = source  # 소스 정보 추가
                all_data.append(item)
                
        print(f"📊 분석할 데이터:")
        print(f"   - 총 {len(all_data)}개 항목")
        for source in collected_data:
            print(f"   - {source}: {len(collected_data[source])}개")
            
        if not all_data:
            print("⚠️ 분석할 데이터가 없습니다")
            await self._send_to_ui(websocket, "log", {"message": "⚠️ 분석할 데이터가 없습니다"})
            return
            
        # 감정 분석 직접 HTTP 호출
        print("🔎 감정 분석 에이전트 직접 호출...")
        
        # UI 업데이트
        await self._send_to_ui(websocket, "status", {"agentId": "sentiment-agent"})
        await self._send_to_ui(websocket, "log", {"message": f"🎯 감정 분석 시작: {len(all_data)}개 항목"})
        await self._send_to_ui(websocket, "log", {"message": "⏳ AI 감성 분석 중입니다. 시간이 소요될 수 있습니다..."})
        
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
                print(f"📤 감정 분석 HTTP 요청 전송 중...")
                print(f"   - URL: http://localhost:8202/analyze_sentiment")
                print(f"   - Ticker: {ticker}")
                print(f"   - Data sources: {list(collected_data.keys())}")
                
                response = await client.post(
                    "http://localhost:8202/analyze_sentiment",
                    json={
                        "ticker": ticker,
                        "data": collected_data  # 딕셔너리 형태로 전송
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ 감정 분석 응답 받음")
                    
                    # 감정 분석 결과 저장
                    session["sentiment_analysis"] = result.get("analyzed_results", [])
                    
                    # UI 업데이트
                    success_count = result.get("success_count", 0)
                    await self._send_to_ui(websocket, "log", {
                        "message": f"✅ 감정 분석 완료: {success_count}개 항목 분석"
                    })
                    
                    # 각 분석 결과의 요약 출력
                    for ticker_data in session["sentiment_analysis"]:
                        source = ticker_data.get("source", "unknown")
                        score = ticker_data.get("score", 0)
                        
                        # 점수를 기반으로 레이블 결정
                        if score > 0.1:
                            label = "positive"
                        elif score < -0.1:
                            label = "negative"
                        else:
                            label = "neutral"
                        
                        emoji = "🟢" if label == "positive" else "🔴" if label == "negative" else "🟡"
                        await self._send_to_ui(websocket, "log", {
                            "message": f"  {emoji} {source}: {label} (점수: {score:.2f})"
                        })
                    
                    # 다음 단계로 진행 (정량적 분석)
                    session["state"] = "quantitative_analysis"
                    await self._start_quantitative_analysis(session)
                    
                else:
                    print(f"❌ 감정 분석 오류: HTTP {response.status_code}")
                    await self._send_to_ui(websocket, "log", {"message": "❌ 감정 분석 오류"})
                    
        except httpx.TimeoutException as e:
            print(f"❌ 감정 분석 타임아웃: {e}")
            await self._send_to_ui(websocket, "log", {"message": "❌ 감정 분석 시간 초과 (AI 분석에 시간이 많이 소요됨)"})
            # 타임아웃이어도 기본 점수로 진행
            # 수집된 데이터를 기본 점수로 변환
            default_sentiments = []
            for source, items in collected_data.items():
                for item in items:
                    default_sentiments.append({
                        "ticker": ticker,
                        "source": source,
                        "title": item.get("title", ""),
                        "content": item.get("content", ""),
                        "score": -0.3 if source == "sec" else -0.5,  # 기본 부정적 점수
                        "summary": "AI 분석 시간 초과로 기본값 사용"
                    })
            session["sentiment_analysis"] = default_sentiments
            # 다음 단계로 진행
            session["state"] = "quantitative_analysis"
            await self._start_quantitative_analysis(session)
        except httpx.ConnectError as e:
            print(f"❌ 감정 분석 연결 실패: {e}")
            await self._send_to_ui(websocket, "log", {"message": "❌ 감정 분석 에이전트 연결 실패"})
            # 연결 실패해도 다음 단계로 진행
            session["state"] = "quantitative_analysis"
            await self._start_quantitative_analysis(session)
        except Exception as e:
            print(f"❌ 감정 분석 예외 발생: {e}")
            import traceback
            traceback.print_exc()
            await self._send_to_ui(websocket, "log", {"message": f"❌ 감정 분석 오류: {str(e)}"})
            
    async def _start_score_calculation(self, session: Dict):
        """점수 계산 시작"""
        print("📊 점수 계산 단계 시작")
        websocket = session["websocket"]
        ticker = session["ticker"]
        sentiment_analysis = session.get("sentiment_analysis", [])
        
        # 세션 ID 찾기
        session_id = None
        for sid, sess in self.analysis_sessions.items():
            if sess == session:
                session_id = sid
                break
                
        if not sentiment_analysis:
            print("⚠️ 점수 계산할 감정 분석 데이터가 없습니다")
            await self._send_to_ui(websocket, "log", {"message": "⚠️ 점수 계산할 데이터가 없습니다"})
            return
            
        # 점수 계산 직접 HTTP 호출
        print("🔎 점수 계산 에이전트 직접 호출...")
        
        # UI 업데이트
        await self._send_to_ui(websocket, "status", {"agentId": "score-agent"})
        await self._send_to_ui(websocket, "log", {"message": f"📊 가중치 기반 점수 계산 시작"})
        
        try:
            async with httpx.AsyncClient() as client:
                print(f"📤 점수 계산 HTTP 요청 전송 중...")
                print(f"📊 전송할 감정 분석 데이터: {len(sentiment_analysis)}개 항목")
                
                response = await client.post(
                    "http://localhost:8203/calculate_score",
                    json={
                        "ticker": ticker,
                        "sentiments": sentiment_analysis  # adapter가 기대하는 키 이름
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ 점수 계산 응답 받음")
                    
                    # 점수 계산 결과 저장
                    session["score_calculation"] = result
                    
                    # 결과 출력
                    final_score = result.get("final_score", 0)
                    final_label = result.get("final_label", "neutral")
                    weighted_scores = result.get("weighted_scores", {})
                    
                    emoji = "🟢" if final_label == "positive" else "🔴" if final_label == "negative" else "🟡"
                    await self._send_to_ui(websocket, "log", {
                        "message": f"✅ 점수 계산 완료"
                    })
                    await self._send_to_ui(websocket, "log", {
                        "message": f"{emoji} 최종 점수: {final_score:.2f} ({final_label})"
                    })
                    
                    # 가중치 적용된 점수 출력
                    for source, score_info in weighted_scores.items():
                        await self._send_to_ui(websocket, "log", {
                            "message": f"  - {source}: {score_info.get('weighted_score', 0):.2f} (가중치: {score_info.get('weight', 0)})"
                        })
                    
                    # 다음 단계로 진행 (리포트 생성)
                    session["state"] = "generating_report"
                    await self._start_report_generation(session)
                    
                else:
                    print(f"❌ 점수 계산 오류: HTTP {response.status_code}")
                    await self._send_to_ui(websocket, "log", {"message": "❌ 점수 계산 오류"})
                    
        except Exception as e:
            print(f"❌ 점수 계산 연결 실패: {e}")
            await self._send_to_ui(websocket, "log", {"message": f"❌ 점수 계산 연결 실패: {str(e)}"})
            
    async def _start_risk_analysis(self, session: Dict):
        """리스크 분석 시작"""
        print("🎯 리스크 분석 단계 시작")
        websocket = session["websocket"]
        ticker = session["ticker"]
        
        # UI 업데이트
        await self._send_to_ui(websocket, "status", {"agentId": "risk-agent"})
        await self._send_to_ui(websocket, "log", {"message": f"⚠️ 리스크 분석 시작"})
        
        # 리스크 분석에 필요한 데이터 준비
        quantitative_data = session.get("quantitative_analysis", {})
        sentiment_data = session.get("sentiment_analysis", [])
        
        try:
            async with httpx.AsyncClient() as client:
                print(f"📤 리스크 분석 HTTP 요청 전송 중...")
                
                response = await client.post(
                    "http://localhost:8212/risk_analysis",
                    json={
                        "ticker": ticker,
                        "quantitative_data": quantitative_data,
                        "sentiment_data": sentiment_data
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ 리스크 분석 응답 받음")
                    
                    # 리스크 분석 결과 저장
                    risk_analysis = result.get("risk_analysis", {})
                    session["risk_analysis"] = risk_analysis
                    
                    # 결과 출력
                    overall_score = risk_analysis.get("overall_risk_score", 0)
                    risk_level = risk_analysis.get("risk_level", "medium")
                    
                    # 리스크 레벨에 따른 이모지
                    risk_emoji = {
                        "very_low": "🟢",
                        "low": "🟢",
                        "medium": "🟡",
                        "high": "🔴",
                        "very_high": "🔴"
                    }.get(risk_level, "🟡")
                    
                    await self._send_to_ui(websocket, "log", {
                        "message": f"✅ 리스크 분석 완료"
                    })
                    await self._send_to_ui(websocket, "log", {
                        "message": f"{risk_emoji} 종합 리스크 점수: {overall_score:.1f}/100 ({risk_level})"
                    })
                    
                    # 주요 리스크 요인 출력
                    market_risk = risk_analysis.get("market_risk", {})
                    company_risk = risk_analysis.get("company_specific_risk", {})
                    sentiment_risk = risk_analysis.get("sentiment_risk", {})
                    liquidity_risk = risk_analysis.get("liquidity_risk", {})
                    
                    await self._send_to_ui(websocket, "log", {
                        "message": f"  - 시장 리스크: {market_risk.get('score', 0):.1f}/100"
                    })
                    await self._send_to_ui(websocket, "log", {
                        "message": f"  - 기업 리스크: {company_risk.get('score', 0):.1f}/100"
                    })
                    await self._send_to_ui(websocket, "log", {
                        "message": f"  - 감성 리스크: {sentiment_risk.get('score', 0):.1f}/100"
                    })
                    await self._send_to_ui(websocket, "log", {
                        "message": f"  - 유동성 리스크: {liquidity_risk.get('score', 0):.1f}/100"
                    })
                    
                    # 권고사항 출력
                    recommendations = risk_analysis.get("recommendations", [])
                    if recommendations:
                        await self._send_to_ui(websocket, "log", {
                            "message": "📋 리스크 권고사항:"
                        })
                        for rec in recommendations[:3]:  # 상위 3개만
                            priority_emoji = "🔴" if rec.get("priority") == "high" else "🟡" if rec.get("priority") == "medium" else "🟢"
                            await self._send_to_ui(websocket, "log", {
                                "message": f"  {priority_emoji} {rec.get('action', '')}: {rec.get('reason', '')}"
                            })
                    
                    # 다음 단계로 진행 (점수 계산)
                    session["state"] = "calculating_score"
                    await self._start_score_calculation(session)
                    
                else:
                    print(f"❌ 리스크 분석 오류: HTTP {response.status_code}")
                    await self._send_to_ui(websocket, "log", {"message": "❌ 리스크 분석 오류"})
                    # 오류가 있어도 다음 단계로 진행
                    session["state"] = "calculating_score"
                    await self._start_score_calculation(session)
                    
        except Exception as e:
            print(f"❌ 리스크 분석 연결 실패: {e}")
            await self._send_to_ui(websocket, "log", {"message": f"❌ 리스크 분석 연결 실패: {str(e)}"})
            # 오류가 있어도 다음 단계로 진행
            session["state"] = "calculating_score"
            await self._start_score_calculation(session)
    
    async def _start_report_generation(self, session: Dict):
        """리포트 생성 시작"""
        print("📝 리포트 생성 단계 시작")
        websocket = session["websocket"]
        ticker = session["ticker"]
        collected_data = session.get("collected_data", {})
        sentiment_analysis = session.get("sentiment_analysis", [])
        score_calculation = session.get("score_calculation", {})
        
        # 세션 ID 찾기
        session_id = None
        for sid, sess in self.analysis_sessions.items():
            if sess == session:
                session_id = sid
                break
                
        # 리포트 생성 직접 HTTP 호출
        print("🔎 리포트 생성 에이전트 직접 호출...")
        
        # UI 업데이트
        await self._send_to_ui(websocket, "status", {"agentId": "report-agent"})
        await self._send_to_ui(websocket, "log", {"message": f"📝 투자 분석 보고서 생성 중..."})
        await self._send_to_ui(websocket, "log", {"message": "⏳ AI가 종합 보고서를 작성 중입니다. 시간이 소요될 수 있습니다..."})
        
        # 리포트 생성을 위한 데이터 준비
        # score_calculation에서 추가 정보 추출
        final_score = score_calculation.get("final_score", 0)
        sentiment = score_calculation.get("sentiment", "neutral")
        score_details = score_calculation.get("details", {})
        
        report_data = {
            "ticker": ticker,
            "company_name": ticker,  # 나중에 실제 회사명으로 대체 가능
            "query": session.get("query", ""),
            "final_score": final_score,
            "sentiment": sentiment,
            "score_details": score_details,
            "sentiment_analysis": sentiment_analysis,  # 감정 분석 원본 데이터
            "quantitative_data": session.get("quantitative_analysis", {}),
            "risk_analysis": session.get("risk_analysis", {}),
            "data_summary": {
                "news": len(collected_data.get("news", [])),
                "twitter": len(collected_data.get("twitter", [])), 
                "sec": len(collected_data.get("sec", []))
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=10.0)) as client:
                print(f"📤 리포트 생성 HTTP 요청 전송 중...")
                print(f"   - Ticker: {ticker}")
                print(f"   - Final Score: {final_score}")
                print(f"   - Sentiment: {sentiment}")
                print(f"   - Data Summary: {report_data['data_summary']}")
                
                # PDF 생성 옵션 확인 (UI에서 전달받거나 세션에 저장)
                generate_pdf = session.get("generate_pdf", False)  # 기본값 False로 HTML 생성
                
                endpoint = "generate_report_pdf" if generate_pdf else "generate_report"
                url = f"http://localhost:8204/{endpoint}"
                print(f"   - URL: {url}")
                
                response = await client.post(
                    url,
                    json=report_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ 리포트 생성 응답 받음")
                    
                    # 리포트 저장
                    session["final_report"] = result.get("report", "")
                    
                    # PDF 경로가 있으면 저장
                    if "pdf_path" in result:
                        session["pdf_path"] = result["pdf_path"]
                        await self._send_to_ui(websocket, "log", {
                            "message": f"📄 PDF 저장 완료: {result['pdf_path']}"
                        })
                    
                    # UI에 최종 결과 전송
                    await self._send_to_ui(websocket, "log", {
                        "message": "✅ 분석 보고서 생성 완료!"
                    })
                    
                    # 최종 결과 전송
                    final_result = {
                        "ticker": session.get("ticker"),
                        "final_score": session.get("score_calculation", {}).get("final_score", 0),
                        "final_label": session.get("score_calculation", {}).get("final_label", "neutral"),
                        "report": session["final_report"],
                        "weighted_scores": session.get("score_calculation", {}).get("weighted_scores", {}),
                        "data_summary": {
                            "news": len(session.get("collected_data", {}).get("news", [])),
                            "twitter": len(session.get("collected_data", {}).get("twitter", [])),
                            "sec": len(session.get("collected_data", {}).get("sec", []))
                        }
                    }
                    
                    # PDF 경로가 있으면 추가
                    if "pdf_path" in session:
                        final_result["pdf_path"] = session["pdf_path"]
                    
                    await self._send_to_ui(websocket, "result", final_result)
                    
                    # 분석 완료 상태
                    session["state"] = "completed"
                    await self._send_to_ui(websocket, "log", {
                        "message": "🎉 전체 분석 프로세스 완료!"
                    })
                    
                else:
                    print(f"❌ 리포트 생성 오류: HTTP {response.status_code}")
                    print(f"   - Response: {response.text[:500]}")
                    await self._send_to_ui(websocket, "log", {"message": f"❌ 리포트 생성 오류 (HTTP {response.status_code})"})
                    
        except httpx.TimeoutException as e:
            print(f"❌ 리포트 생성 타임아웃: {e}")
            await self._send_to_ui(websocket, "log", {"message": "❌ 리포트 생성 시간 초과"})
        except httpx.ConnectError as e:
            print(f"❌ 리포트 생성 연결 실패: {e}")
            await self._send_to_ui(websocket, "log", {"message": "❌ 리포트 생성 에이전트 연결 실패"})
        except Exception as e:
            print(f"❌ 리포트 생성 예외 발생: {e}")
            import traceback
            traceback.print_exc()
            await self._send_to_ui(websocket, "log", {"message": f"❌ 리포트 생성 오류: {str(e)}"})
            
    async def _handle_event(self, event_type: str, message: A2AMessage):
        """이벤트 처리"""
        event_data = message.body.get("event_data", {})
        
        if event_type == "ticker_extracted":
            # 티커 추출 이벤트
            ticker = event_data.get("ticker")
            print(f"📢 티커 추출 이벤트: {ticker}")
            
        elif event_type == "data_collected":
            # 데이터 수집 완료 이벤트
            source = event_data.get("source")
            count = event_data.get("count")
            print(f"📢 데이터 수집 완료: {source} ({count}개)")
            
        elif event_type == "report_generated":
            # 리포트 생성 완료 이벤트
            print(f"📢 리포트 생성 완료 이벤트 수신!")
            ticker = event_data.get("ticker")
            recommendation = event_data.get("recommendation")
            report = event_data.get("report", "")
            summary = event_data.get("summary", "")
            
            # 모든 활성 세션에 브로드캐스트
            for session_id, session in self.analysis_sessions.items():
                if session.get("ticker") == ticker and session.get("websocket"):
                    websocket = session["websocket"]
                    try:
                        await self._send_to_ui(websocket, "log", {
                            "message": "🎉 전체 분석 프로세스 완료!"
                        })
                        
                        # report_generated 타입으로 최종 리포트 전송
                        await self._send_to_ui(websocket, "report_generated", {
                            "report": report,  # 이벤트에서 받은 실제 리포트 사용
                            "ticker": ticker,
                            "recommendation": recommendation,
                            "summary": summary
                        })
                    except Exception as e:
                        print(f"❌ 이벤트 브로드캐스트 실패: {e}")
            
        # 추가 이벤트 처리...
        
    async def _send_to_ui(self, websocket: WebSocket, msg_type: str, payload: Dict[str, Any]):
        """UI로 메시지 전송"""
        try:
            message = {"type": msg_type, "payload": payload}
            print(f"🖥️ UI로 메시지 전송: {message}")
            await websocket.send_json(message)
            print("✅ UI 전송 성공")
        except Exception as e:
            print(f"❌ UI 전송 실패: {e}")
            import traceback
            traceback.print_exc()


# 모듈 레벨에서 오케스트레이터와 app 생성
orchestrator = OrchestratorV2()
app = orchestrator.app  # uvicorn이 찾을 수 있도록 app 객체 노출
print(f"✅ {orchestrator.name} 초기화 완료")

# HTTP 엔드포인트 추가
@app.post("/analyze")
async def analyze_query(request: dict):
    """HTTP POST로 분석 요청 처리"""
    query = request.get("query", "")
    if not query:
        return {"error": "Query is required"}, 400
    
    # 임시 세션 ID 생성
    import time
    session_id = f"http-{time.time()}"
    
    # WebSocket 없이 분석 수행을 위한 간단한 구현
    return {
        "message": "V2 시스템은 WebSocket을 통해 작동합니다. http://localhost:8100 에서 UI를 사용해주세요.",
        "query": query,
        "session_id": session_id
    }


@app.on_event("startup")
async def startup():
    await orchestrator.start()


@app.on_event("shutdown")
async def shutdown():
    await orchestrator.stop()


# 독립 실행용
if __name__ == "__main__":
    orchestrator.run()