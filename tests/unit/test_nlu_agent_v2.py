"""
NLU Agent V2 단위 테스트

TDD 방식으로 작성된 자연어 이해 에이전트 테스트
"""

import pytest
import os
from unittest.mock import Mock, patch, AsyncMock
from agents.nlu_agent_v2 import NLUAgentV2
from a2a_core.protocols.message import A2AMessage, MessageType


class TestNLUAgentV2:
    """NLU Agent V2 테스트"""
    
    @pytest.fixture
    def nlu_agent(self):
        """NLU 에이전트 fixture"""
        # 환경 변수 설정
        os.environ["GEMINI_API_KEY"] = "test-api-key"
        return NLUAgentV2()
        
    def test_nlu_agent_initialization(self, nlu_agent):
        """NLU 에이전트 초기화 테스트"""
        # Then: 올바르게 초기화되어야 함
        assert nlu_agent.name == "NLU Agent V2"
        assert nlu_agent.port == 8108
        assert nlu_agent.ticker_map["애플"] == "AAPL"
        assert nlu_agent.ticker_map["테슬라"] == "TSLA"
        assert nlu_agent.gemini_api_key == "test-api-key"
        
    @pytest.mark.asyncio
    async def test_on_start_capability_registration(self, nlu_agent):
        """시작 시 능력 등록 테스트"""
        # When: 에이전트를 시작하면
        await nlu_agent.on_start()
        
        # Then: 티커 추출 능력이 등록되어야 함
        assert len(nlu_agent.capabilities) == 1
        capability = nlu_agent.capabilities[0]
        assert capability["name"] == "extract_ticker"
        assert capability["version"] == "2.0"
        assert "input_schema" in capability
        assert "output_schema" in capability
        
    @pytest.mark.asyncio
    async def test_handle_extract_ticker_with_keyword(self, nlu_agent):
        """키워드 기반 티커 추출 테스트"""
        # Given: 애플을 언급하는 메시지
        message = A2AMessage.create_request(
            sender_id="test-sender",
            receiver_id=nlu_agent.agent_id,
            action="extract_ticker",
            payload={"query": "애플 주가가 어떻게 되나요?"}
        )
        
        # Mock reply_to_message
        nlu_agent.reply_to_message = AsyncMock()
        nlu_agent.broadcast_event = AsyncMock()
        
        # When: 메시지를 처리하면
        await nlu_agent.handle_message(message)
        
        # Then: 티커가 추출되어야 함
        reply_call = nlu_agent.reply_to_message.call_args
        result = reply_call[1]["result"]
        assert result["ticker"] == "AAPL"
        assert result["company_name"] == "애플"
        assert result["confidence"] == 0.95
        assert "추출했습니다" in result["log_message"]
        
        # 이벤트가 브로드캐스트되어야 함
        event_call = nlu_agent.broadcast_event.call_args
        assert event_call[1]["event_type"] == "ticker_extracted"
        assert event_call[1]["event_data"]["ticker"] == "AAPL"
        
    @pytest.mark.asyncio
    async def test_handle_extract_ticker_with_gemini(self, nlu_agent):
        """Gemini API를 사용한 티커 추출 테스트"""
        # Given: 키워드에 없는 회사 질문
        message = A2AMessage.create_request(
            sender_id="test-sender",
            receiver_id=nlu_agent.agent_id,
            action="extract_ticker",
            payload={"query": "스타벅스 실적이 어떤가요?"}
        )
        
        # Mock Gemini API 응답
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "candidates": [{
                    "content": {
                        "parts": [{
                            "text": '{"ticker": "SBUX", "company_name": "스타벅스", "confidence": 0.9}'
                        }]
                    }
                }]
            }
            mock_client.post.return_value = mock_response
            
            nlu_agent.reply_to_message = AsyncMock()
            nlu_agent.broadcast_event = AsyncMock()
            
            # When: 메시지를 처리하면
            await nlu_agent.handle_message(message)
            
            # Then: Gemini API가 호출되고 결과가 반환되어야 함
            mock_client.post.assert_called()
            api_call = mock_client.post.call_args
            assert "generativelanguage.googleapis.com" in api_call[0][0]
            
            reply_call = nlu_agent.reply_to_message.call_args
            result = reply_call[1]["result"]
            assert result["ticker"] == "SBUX"
            assert result["company_name"] == "스타벅스"
            
    @pytest.mark.asyncio
    async def test_handle_extract_ticker_not_found(self, nlu_agent):
        """티커를 찾을 수 없는 경우 테스트"""
        # Given: 회사와 관련 없는 질문
        message = A2AMessage.create_request(
            sender_id="test-sender",
            receiver_id=nlu_agent.agent_id,
            action="extract_ticker",
            payload={"query": "오늘 날씨가 어떻습니까?"}
        )
        
        nlu_agent.reply_to_message = AsyncMock()
        nlu_agent.broadcast_event = AsyncMock()
        
        # When: 메시지를 처리하면
        await nlu_agent.handle_message(message)
        
        # Then: 티커를 찾을 수 없다는 응답
        reply_call = nlu_agent.reply_to_message.call_args
        result = reply_call[1]["result"]
        assert result["ticker"] is None
        assert "error" in result
        assert "찾을 수 없습니다" in result["log_message"]
        assert reply_call[1]["success"] is False
        
        # 이벤트는 브로드캐스트되지 않아야 함
        nlu_agent.broadcast_event.assert_not_called()
        
    @pytest.mark.asyncio
    async def test_handle_unsupported_action(self, nlu_agent):
        """지원하지 않는 액션 처리 테스트"""
        # Given: 지원하지 않는 액션
        message = A2AMessage.create_request(
            sender_id="test-sender",
            receiver_id=nlu_agent.agent_id,
            action="unsupported_action",
            payload={}
        )
        
        nlu_agent.reply_to_message = AsyncMock()
        
        # When: 메시지를 처리하면
        await nlu_agent.handle_message(message)
        
        # Then: 에러 응답이 반환되어야 함
        reply_call = nlu_agent.reply_to_message.call_args
        result = reply_call[1]["result"]
        assert "error" in result
        assert "Unsupported action" in result["error"]
        assert reply_call[1]["success"] is False
        
    @pytest.mark.asyncio
    async def test_handle_event_message(self, nlu_agent):
        """이벤트 메시지 처리 테스트"""
        # Given: 이벤트 메시지
        event_message = A2AMessage.create_event(
            sender_id="other-agent",
            event_type="system_update",
            event_data={"version": "2.0"}
        )
        
        # When: 이벤트 메시지를 처리하면
        with patch('builtins.print') as mock_print:
            await nlu_agent.handle_message(event_message)
            
            # Then: 이벤트가 로깅되어야 함
            mock_print.assert_called()
            print_call = mock_print.call_args[0][0]
            assert "이벤트 수신" in print_call
            assert "system_update" in print_call
            
    @pytest.mark.asyncio
    async def test_gemini_api_error_handling(self, nlu_agent):
        """Gemini API 오류 처리 테스트"""
        # Given: API 오류 상황
        message = A2AMessage.create_request(
            sender_id="test-sender",
            receiver_id=nlu_agent.agent_id,
            action="extract_ticker",
            payload={"query": "마이크로소프트 전망"}
        )
        
        # Mock Gemini API 오류
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.side_effect = Exception("API Error")
            
            nlu_agent.reply_to_message = AsyncMock()
            
            # When: 메시지를 처리하면
            await nlu_agent.handle_message(message)
            
            # Then: 기본 키워드 매칭으로 폴백
            reply_call = nlu_agent.reply_to_message.call_args
            result = reply_call[1]["result"]
            assert result["ticker"] == "MSFT"  # 키워드 매칭 결과
            assert result["company_name"] == "마이크로소프트"
            
    @pytest.mark.asyncio
    async def test_multiple_company_mentions(self, nlu_agent):
        """여러 회사가 언급된 경우 테스트"""
        # Given: 여러 회사를 언급하는 질문
        message = A2AMessage.create_request(
            sender_id="test-sender",
            receiver_id=nlu_agent.agent_id,
            action="extract_ticker",
            payload={"query": "애플과 구글 중 어떤 것이 더 좋을까요?"}
        )
        
        nlu_agent.reply_to_message = AsyncMock()
        nlu_agent.broadcast_event = AsyncMock()
        
        # When: 메시지를 처리하면
        await nlu_agent.handle_message(message)
        
        # Then: 첫 번째로 매칭된 회사가 반환
        reply_call = nlu_agent.reply_to_message.call_args
        result = reply_call[1]["result"]
        assert result["ticker"] in ["AAPL", "GOOGL"]  # 둘 중 하나
        
    def test_ticker_map_completeness(self, nlu_agent):
        """티커 맵 완성도 테스트"""
        # Then: 주요 회사들이 포함되어야 함
        expected_companies = ["애플", "삼성", "테슬라", "구글", "아마존"]
        for company in expected_companies:
            assert company in nlu_agent.ticker_map
            assert nlu_agent.ticker_map[company] is not None