"""
WebSocket 연결 관리 및 재연결 로직
자동 재연결, 하트비트, 연결 상태 관리 기능 제공
"""
import asyncio
import logging
from typing import Optional, Callable, Dict, Any
from datetime import datetime
import json
from fastapi import WebSocket, WebSocketDisconnect
from enum import Enum

from utils.config_manager import config
from utils.errors import WebSocketError

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """WebSocket 연결 상태"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    CLOSED = "closed"


class WebSocketManager:
    """WebSocket 연결 관리 클래스"""
    
    def __init__(
        self,
        websocket: WebSocket,
        client_id: str,
        on_message: Optional[Callable] = None,
        on_disconnect: Optional[Callable] = None
    ):
        self.websocket = websocket
        self.client_id = client_id
        self.on_message = on_message
        self.on_disconnect = on_disconnect
        
        # 설정 로드
        ws_config = config.get("orchestrator", {})
        self.heartbeat_interval = ws_config.get("heartbeat_interval", 30)
        self.reconnect_interval = ws_config.get("reconnect_interval", 5)
        self.max_reconnect_attempts = ws_config.get("max_reconnect_attempts", 5)
        
        # 상태 관리
        self.state = ConnectionState.DISCONNECTED
        self.connected_at: Optional[datetime] = None
        self.last_heartbeat: Optional[datetime] = None
        self.reconnect_attempts = 0
        
        # 태스크 관리
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.receive_task: Optional[asyncio.Task] = None
        
        # 통계
        self.messages_sent = 0
        self.messages_received = 0
        self.total_reconnects = 0
        
    async def connect(self):
        """WebSocket 연결 시작"""
        try:
            self.state = ConnectionState.CONNECTING
            await self.websocket.accept()
            
            self.state = ConnectionState.CONNECTED
            self.connected_at = datetime.now()
            self.reconnect_attempts = 0
            
            logger.info(f"✅ WebSocket 연결 성공: {self.client_id}")
            
            # 하트비트 시작
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            # 메시지 수신 시작
            self.receive_task = asyncio.create_task(self._receive_loop())
            
            # 연결 성공 메시지 전송
            await self.send_json({
                "type": "connection",
                "status": "connected",
                "client_id": self.client_id,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ WebSocket 연결 실패: {e}")
            self.state = ConnectionState.DISCONNECTED
            raise WebSocketError(f"Connection failed: {str(e)}")
    
    async def disconnect(self):
        """WebSocket 연결 종료"""
        self.state = ConnectionState.CLOSED
        
        # 태스크 취소
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        if self.receive_task:
            self.receive_task.cancel()
        
        try:
            await self.websocket.close()
        except:
            pass
        
        # 콜백 호출
        if self.on_disconnect:
            await self.on_disconnect(self.client_id)
        
        logger.info(f"👋 WebSocket 연결 종료: {self.client_id}")
    
    async def send_json(self, data: Dict[str, Any]):
        """JSON 메시지 전송"""
        if self.state != ConnectionState.CONNECTED:
            raise WebSocketError(f"Not connected (state: {self.state.value})")
        
        try:
            await self.websocket.send_json(data)
            self.messages_sent += 1
            
        except Exception as e:
            logger.error(f"❌ 메시지 전송 실패: {e}")
            await self._handle_disconnect()
            raise
    
    async def send_text(self, text: str):
        """텍스트 메시지 전송"""
        if self.state != ConnectionState.CONNECTED:
            raise WebSocketError(f"Not connected (state: {self.state.value})")
        
        try:
            await self.websocket.send_text(text)
            self.messages_sent += 1
            
        except Exception as e:
            logger.error(f"❌ 메시지 전송 실패: {e}")
            await self._handle_disconnect()
            raise
    
    async def _heartbeat_loop(self):
        """하트비트 전송 루프"""
        while self.state == ConnectionState.CONNECTED:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                # 하트비트 전송
                await self.websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat()
                })
                
                self.last_heartbeat = datetime.now()
                logger.debug(f"💓 하트비트 전송: {self.client_id}")
                
            except Exception as e:
                logger.error(f"❌ 하트비트 실패: {e}")
                await self._handle_disconnect()
                break
    
    async def _receive_loop(self):
        """메시지 수신 루프"""
        while self.state == ConnectionState.CONNECTED:
            try:
                # 메시지 수신
                message = await self.websocket.receive_json()
                self.messages_received += 1
                
                # 하트비트 응답 처리
                if message.get("type") == "heartbeat":
                    logger.debug(f"💓 하트비트 응답 수신: {self.client_id}")
                    continue
                
                # 메시지 콜백 호출
                if self.on_message:
                    await self.on_message(self.client_id, message)
                
            except WebSocketDisconnect:
                logger.info(f"🔌 WebSocket 연결 끊김: {self.client_id}")
                await self._handle_disconnect()
                break
                
            except Exception as e:
                logger.error(f"❌ 메시지 수신 오류: {e}")
                await self._handle_disconnect()
                break
    
    async def _handle_disconnect(self):
        """연결 끊김 처리"""
        if self.state in [ConnectionState.CLOSED, ConnectionState.RECONNECTING]:
            return
        
        self.state = ConnectionState.DISCONNECTED
        
        # 태스크 취소
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        if self.receive_task:
            self.receive_task.cancel()
        
        # 재연결 시도
        if self.reconnect_attempts < self.max_reconnect_attempts:
            await self._attempt_reconnect()
        else:
            logger.error(f"❌ 최대 재연결 시도 횟수 초과: {self.client_id}")
            self.state = ConnectionState.CLOSED
            if self.on_disconnect:
                await self.on_disconnect(self.client_id)
    
    async def _attempt_reconnect(self):
        """재연결 시도"""
        self.state = ConnectionState.RECONNECTING
        self.reconnect_attempts += 1
        self.total_reconnects += 1
        
        logger.info(
            f"🔄 재연결 시도 {self.reconnect_attempts}/{self.max_reconnect_attempts}: "
            f"{self.client_id}"
        )
        
        # 재연결 대기
        await asyncio.sleep(self.reconnect_interval * self.reconnect_attempts)
        
        try:
            # 재연결 시도
            await self.connect()
            logger.info(f"✅ 재연결 성공: {self.client_id}")
            
        except Exception as e:
            logger.error(f"❌ 재연결 실패: {e}")
            await self._handle_disconnect()
    
    def get_stats(self) -> Dict[str, Any]:
        """연결 통계 반환"""
        uptime = None
        if self.connected_at and self.state == ConnectionState.CONNECTED:
            uptime = (datetime.now() - self.connected_at).total_seconds()
        
        return {
            "client_id": self.client_id,
            "state": self.state.value,
            "connected_at": self.connected_at.isoformat() if self.connected_at else None,
            "uptime_seconds": uptime,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "reconnect_attempts": self.reconnect_attempts,
            "total_reconnects": self.total_reconnects
        }


class WebSocketPool:
    """WebSocket 연결 풀 관리"""
    
    def __init__(self):
        self.connections: Dict[str, WebSocketManager] = {}
        self.lock = asyncio.Lock()
        
    async def add_connection(
        self,
        websocket: WebSocket,
        client_id: str,
        on_message: Optional[Callable] = None,
        on_disconnect: Optional[Callable] = None
    ) -> WebSocketManager:
        """연결 추가"""
        async with self.lock:
            # 기존 연결이 있으면 종료
            if client_id in self.connections:
                await self.remove_connection(client_id)
            
            # 새 연결 생성
            manager = WebSocketManager(
                websocket,
                client_id,
                on_message,
                on_disconnect
            )
            
            # 연결 시작
            await manager.connect()
            
            # 풀에 추가
            self.connections[client_id] = manager
            
            logger.info(f"📊 연결 풀에 추가: {client_id} (총 {len(self.connections)}개)")
            
            return manager
    
    async def remove_connection(self, client_id: str):
        """연결 제거"""
        async with self.lock:
            if client_id in self.connections:
                manager = self.connections[client_id]
                await manager.disconnect()
                del self.connections[client_id]
                
                logger.info(f"📊 연결 풀에서 제거: {client_id} (총 {len(self.connections)}개)")
    
    async def broadcast(self, message: Dict[str, Any], exclude: Optional[str] = None):
        """모든 연결에 브로드캐스트"""
        disconnected = []
        
        for client_id, manager in self.connections.items():
            if exclude and client_id == exclude:
                continue
            
            try:
                await manager.send_json(message)
            except:
                disconnected.append(client_id)
        
        # 실패한 연결 제거
        for client_id in disconnected:
            await self.remove_connection(client_id)
    
    async def send_to_client(self, client_id: str, message: Dict[str, Any]):
        """특정 클라이언트에 메시지 전송"""
        if client_id in self.connections:
            try:
                await self.connections[client_id].send_json(message)
            except:
                await self.remove_connection(client_id)
                raise
        else:
            raise WebSocketError(f"Client not found: {client_id}")
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """모든 연결의 통계 반환"""
        return {
            client_id: manager.get_stats()
            for client_id, manager in self.connections.items()
        }
    
    async def close_all(self):
        """모든 연결 종료"""
        async with self.lock:
            for client_id in list(self.connections.keys()):
                await self.remove_connection(client_id)
            
            logger.info("🔌 모든 WebSocket 연결 종료")


# 전역 연결 풀
websocket_pool = WebSocketPool()


# 편의 함수들
async def manage_websocket(
    websocket: WebSocket,
    client_id: str,
    on_message: Optional[Callable] = None,
    on_disconnect: Optional[Callable] = None
) -> WebSocketManager:
    """WebSocket 연결 관리 시작"""
    return await websocket_pool.add_connection(
        websocket,
        client_id,
        on_message,
        on_disconnect
    )


async def broadcast_message(message: Dict[str, Any], exclude: Optional[str] = None):
    """모든 클라이언트에 메시지 브로드캐스트"""
    await websocket_pool.broadcast(message, exclude)


async def send_to_client(client_id: str, message: Dict[str, Any]):
    """특정 클라이언트에 메시지 전송"""
    await websocket_pool.send_to_client(client_id, message)