"""
A2A 메시지 프로토콜 단위 테스트

TDD 방식으로 작성된 메시지 형식 및 동작 테스트
"""

import pytest
from datetime import datetime, timedelta
from a2a_core.protocols.message import (
    A2AMessage, MessageHeader, MessageMetadata,
    MessageType, Priority
)


class TestMessageProtocol:
    """메시지 프로토콜 테스트"""
    
    def test_create_request_message(self):
        """요청 메시지 생성 테스트"""
        # When: 요청 메시지를 생성하면
        message = A2AMessage.create_request(
            sender_id="agent-1",
            receiver_id="agent-2",
            action="analyze_data",
            payload={"data": "test"}
        )
        
        # Then: 올바른 구조를 가져야 함
        assert message.header.sender_id == "agent-1"
        assert message.header.receiver_id == "agent-2"
        assert message.header.message_type == MessageType.REQUEST
        assert message.body["action"] == "analyze_data"
        assert message.body["payload"] == {"data": "test"}
        assert message.header.protocol_version == "1.0"
        
    def test_create_response_message(self):
        """응답 메시지 생성 테스트"""
        # Given: 원본 요청 메시지
        request = A2AMessage.create_request(
            sender_id="agent-1",
            receiver_id="agent-2",
            action="get_data",
            payload={}
        )
        
        # When: 응답 메시지를 생성하면
        response = A2AMessage.create_response(
            original_message=request,
            sender_id="agent-2",
            result={"status": "success", "data": [1, 2, 3]},
            success=True
        )
        
        # Then: 요청과 연결된 응답이어야 함
        assert response.header.sender_id == "agent-2"
        assert response.header.receiver_id == "agent-1"  # 원 발신자에게 응답
        assert response.header.message_type == MessageType.RESPONSE
        assert response.header.correlation_id == request.header.message_id
        assert response.body["success"] is True
        assert response.body["result"]["data"] == [1, 2, 3]
        assert response.body["original_action"] == "get_data"
        
    def test_create_error_message(self):
        """에러 메시지 생성 테스트"""
        # When: 에러 메시지를 생성하면
        error = A2AMessage.create_error(
            sender_id="agent-1",
            receiver_id="agent-2",
            error_code="INVALID_ACTION",
            error_message="Unknown action requested",
            correlation_id="original-msg-id"
        )
        
        # Then: 에러 정보를 포함해야 함
        assert error.header.message_type == MessageType.ERROR
        assert error.body["error_code"] == "INVALID_ACTION"
        assert error.body["error_message"] == "Unknown action requested"
        assert error.header.correlation_id == "original-msg-id"
        assert "timestamp" in error.body
        
    def test_create_event_message(self):
        """이벤트 메시지 생성 테스트"""
        # When: 이벤트 메시지를 생성하면
        event = A2AMessage.create_event(
            sender_id="agent-1",
            event_type="data_updated",
            event_data={"table": "users", "count": 5}
        )
        
        # Then: 브로드캐스트용 이벤트여야 함
        assert event.header.message_type == MessageType.EVENT
        assert event.header.receiver_id is None  # 브로드캐스트
        assert event.body["event_type"] == "data_updated"
        assert event.body["event_data"]["count"] == 5
        assert "timestamp" in event.body
        
    def test_message_priority(self):
        """메시지 우선순위 테스트"""
        # When: 다양한 우선순위로 메시지 생성
        low_priority = A2AMessage.create_request(
            sender_id="agent-1",
            receiver_id="agent-2",
            action="low_priority_task",
            payload={}
        )
        low_priority.metadata.priority = Priority.LOW
        
        urgent_message = A2AMessage.create_request(
            sender_id="agent-1",
            receiver_id="agent-2",
            action="urgent_task",
            payload={}
        )
        urgent_message.metadata.priority = Priority.URGENT
        
        # Then: 우선순위가 올바르게 설정되어야 함
        assert low_priority.metadata.priority == Priority.LOW
        assert urgent_message.metadata.priority == Priority.URGENT
        
    def test_message_ttl_expiration(self):
        """메시지 TTL 만료 테스트"""
        # Given: TTL이 설정된 메시지
        message = A2AMessage.create_request(
            sender_id="agent-1",
            receiver_id="agent-2",
            action="time_sensitive",
            payload={}
        )
        message.metadata.ttl = 2  # 2초
        
        # When: 시간이 지나지 않았을 때
        assert not message.is_expired()
        
        # When: TTL을 초과한 시간이 지났을 때
        message.header.timestamp = datetime.now() - timedelta(seconds=3)
        
        # Then: 만료되어야 함
        assert message.is_expired()
        
    def test_message_retry_logic(self):
        """메시지 재시도 로직 테스트"""
        # Given: 재시도 가능한 메시지
        message = A2AMessage.create_request(
            sender_id="agent-1",
            receiver_id="agent-2",
            action="retry_task",
            payload={}
        )
        message.metadata.max_retries = 3
        
        # When: 재시도 횟수가 한계 내일 때
        assert message.should_retry()
        assert message.metadata.retry_count == 0
        
        # When: 재시도 증가
        message.increment_retry()
        assert message.metadata.retry_count == 1
        assert message.should_retry()
        
        # When: 최대 재시도 도달
        message.metadata.retry_count = 3
        assert not message.should_retry()
        
    def test_message_to_dict_conversion(self):
        """메시지를 딕셔너리로 변환 테스트"""
        # Given: 복잡한 메시지
        message = A2AMessage.create_request(
            sender_id="agent-1",
            receiver_id="agent-2",
            action="complex_action",
            payload={"nested": {"data": [1, 2, 3]}}
        )
        message.metadata.priority = Priority.HIGH
        message.metadata.tags = ["important", "financial"]
        
        # When: 딕셔너리로 변환
        msg_dict = message.to_dict()
        
        # Then: 모든 필드가 포함되어야 함
        assert msg_dict["header"]["sender_id"] == "agent-1"
        assert msg_dict["header"]["receiver_id"] == "agent-2"
        assert msg_dict["header"]["message_type"] == "request"
        assert msg_dict["body"]["payload"]["nested"]["data"] == [1, 2, 3]
        assert msg_dict["metadata"]["priority"] == "high"
        assert msg_dict["metadata"]["tags"] == ["important", "financial"]
        
    def test_message_with_acknowledgment(self):
        """확인 응답이 필요한 메시지 테스트"""
        # When: ACK가 필요한 메시지 생성
        message = A2AMessage.create_request(
            sender_id="agent-1",
            receiver_id="agent-2",
            action="important_action",
            payload={}
        )
        message.metadata.require_ack = True
        
        # Then: ACK 플래그가 설정되어야 함
        assert message.metadata.require_ack is True
        
    def test_message_header_defaults(self):
        """메시지 헤더 기본값 테스트"""
        # When: 헤더 생성
        header = MessageHeader(
            sender_id="agent-1",
            message_type=MessageType.REQUEST
        )
        
        # Then: 기본값이 올바르게 설정되어야 함
        assert header.message_id is not None
        assert len(header.message_id) == 36  # UUID
        assert header.timestamp is not None
        assert header.protocol_version == "1.0"
        assert header.receiver_id is None
        assert header.correlation_id is None
        
    def test_message_metadata_defaults(self):
        """메시지 메타데이터 기본값 테스트"""
        # When: 메타데이터 생성
        metadata = MessageMetadata()
        
        # Then: 기본값이 올바르게 설정되어야 함
        assert metadata.priority == Priority.NORMAL
        assert metadata.ttl is None
        assert metadata.retry_count == 0
        assert metadata.max_retries == 3
        assert metadata.require_ack is False
        assert metadata.tags == []