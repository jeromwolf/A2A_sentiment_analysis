# A2A (Agent-to-Agent) 프로토콜 5대 설계 원칙

## 🎯 개요
A2A 프로토콜은 2025년 4월 구글에 의해 제안된 AI 에이전트 간 상호운용성을 위한 핵심 프로토콜입니다. 다양한 벤더와 프레임워크의 에이전트들이 자유롭게 협업할 수 있도록 설계되었습니다.

## 📐 5대 설계 원칙

### 1. 에이전트 본연의 능력 포용 (Embrace Agentic Capabilities) 🤖

#### 핵심 개념
- 에이전트를 단순한 "도구"로 제한하지 않고 자율적 주체로 인정
- 메모리, 도구 사용 등을 명시적으로 노출하지 않아도 자연스러운 협업 가능

#### 실제 적용
```python
# 에이전트가 내부적으로 메모리와 도구를 관리
class AutonomousAgent:
    def __init__(self):
        self._memory = {}  # 내부 메모리 (노출 안 함)
        self._tools = []   # 내부 도구 (노출 안 함)
    
    async def collaborate(self, message: A2AMessage):
        # 자율적으로 메모리와 도구를 활용하여 응답
        context = self._retrieve_context(message)
        result = await self._process_with_tools(message, context)
        return result
```

#### 장점
- 각 에이전트가 독립적으로 진화 가능
- 복잡한 내부 구현을 숨기고 간단한 인터페이스 제공
- 진정한 멀티 에이전트 시나리오 구현

### 2. 기존 웹 표준 활용 (Build on Web Standards) 🌐

#### 핵심 개념
- HTTP/HTTPS, JSON-RPC 등 검증된 웹 표준 기반
- 새로운 프로토콜을 만들지 않고 기존 인프라 활용

#### 실제 적용
```python
# JSON-RPC 2.0 기반 메시지 형식
{
    "jsonrpc": "2.0",
    "method": "analyze_sentiment",
    "params": {
        "text": "애플 주가가 상승세를 보이고 있습니다",
        "source": "news"
    },
    "id": "req-123"
}

# HTTP 헤더 활용
headers = {
    "Content-Type": "application/json",
    "X-Agent-Name": "sentiment_analyzer",
    "X-Correlation-ID": "task-456"
}
```

#### 장점
- 개발자들이 이미 익숙한 기술 스택
- 기존 도구와 라이브러리 재사용 가능
- 방화벽, 프록시 등 기존 인프라와 호환

### 3. 기본적 보안 확보 (Secure by Default) 🔒

#### 핵심 개념
- OAuth 2.0, JWT 등 표준 인증 메커니즘 지원
- 엔터프라이즈급 보안 요구사항 충족

#### 실제 적용
```python
class SecureA2AClient:
    def __init__(self):
        self.oauth_client = OAuth2Client()
        
    async def send_message(self, agent_url: str, message: dict):
        # OAuth 토큰 자동 갱신
        token = await self.oauth_client.get_access_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Agent-Signature": self._sign_message(message)
        }
        
        # TLS 암호화된 연결
        async with aiohttp.ClientSession() as session:
            async with session.post(
                agent_url,
                headers=headers,
                json=message,
                ssl=True
            ) as response:
                return await response.json()
```

#### 보안 기능
- **인증 (Authentication)**: OAuth 2.0, API Keys
- **권한 부여 (Authorization)**: 역할 기반 접근 제어
- **암호화 (Encryption)**: TLS 1.3+
- **감사 추적 (Audit Trail)**: 모든 통신 로깅

### 4. 장기 실행 작업 지원 (Long-Running Tasks) ⏱️

#### 핵심 개념
- 수 시간 또는 수일이 걸리는 작업 지원
- 인간 개입이 필요한 워크플로우 처리

#### 실제 적용
```python
class LongRunningTaskHandler:
    async def start_analysis(self, request: AnalysisRequest) -> str:
        # 작업 시작하고 즉시 task_id 반환
        task_id = str(uuid.uuid4())
        
        # 백그라운드에서 작업 실행
        asyncio.create_task(self._process_long_task(task_id, request))
        
        return task_id
    
    async def get_status(self, task_id: str) -> TaskStatus:
        return {
            "task_id": task_id,
            "status": self.tasks[task_id]["status"],
            "progress": self.tasks[task_id]["progress"],
            "estimated_completion": self.tasks[task_id]["eta"]
        }
    
    async def stream_updates(self, task_id: str):
        """실시간 업데이트 스트리밍"""
        while not self.tasks[task_id]["completed"]:
            yield self.tasks[task_id]["current_update"]
            await asyncio.sleep(1)
```

#### 지원 기능
- **비동기 처리**: 작업 ID 기반 추적
- **진행 상황 모니터링**: 실시간 업데이트
- **중간 결과 스트리밍**: Server-Sent Events
- **작업 취소/재개**: 유연한 작업 제어

### 5. 모달리티 무관 (Modality-Agnostic) 📡

#### 핵심 개념
- 텍스트, 이미지, 오디오, 파일 등 다양한 데이터 형식 지원
- 메시지 형식에 구애받지 않는 통신

#### 실제 적용
```python
class MultiModalMessage:
    def __init__(self):
        self.parts = []
    
    def add_text(self, text: str):
        self.parts.append({
            "type": "text",
            "content": text
        })
    
    def add_image(self, image_data: bytes, mime_type: str):
        self.parts.append({
            "type": "image",
            "content": base64.b64encode(image_data).decode(),
            "mime_type": mime_type
        })
    
    def add_file(self, file_path: str):
        self.parts.append({
            "type": "file",
            "path": file_path,
            "name": os.path.basename(file_path)
        })
    
    def add_data(self, data: dict):
        self.parts.append({
            "type": "data",
            "content": data
        })
```

#### 지원 모달리티
- **TextPart**: 일반 텍스트 메시지
- **ImagePart**: 이미지 데이터 (차트, 그래프 등)
- **FilePart**: 문서, 스프레드시트 등
- **DataPart**: 구조화된 데이터 (JSON, CSV)
- **AudioPart**: 음성 메시지 (향후 지원)

## 🚀 실전 적용 예시

### 켈리님 프로젝트에서의 구현
```python
class A2ASentimentAgent:
    """A2A 원칙을 따르는 감성 분석 에이전트"""
    
    def __init__(self):
        # 1. 에이전트 능력 포용
        self.internal_memory = {}
        self.llm_manager = LLMManager()
        
        # 3. 기본적 보안
        self.auth = OAuth2Handler()
        
    async def handle_request(self, message: dict):
        # 2. 웹 표준 활용 (JSON-RPC)
        if message.get("jsonrpc") != "2.0":
            return {"error": "Invalid JSON-RPC version"}
        
        # 4. 장기 실행 작업
        if self._is_large_analysis(message):
            task_id = await self._start_async_task(message)
            return {
                "jsonrpc": "2.0",
                "result": {"task_id": task_id},
                "id": message.get("id")
            }
        
        # 5. 모달리티 무관
        result = await self._process_multimodal(message["params"])
        
        return {
            "jsonrpc": "2.0",
            "result": result,
            "id": message.get("id")
        }
```

## 📊 A2A vs 전통적 접근법

| 측면 | 전통적 접근법 | A2A 프로토콜 |
|------|---------------|--------------|
| 통합 복잡도 | N×M (각 조합마다 커스텀) | 1×N (표준 프로토콜) |
| 에이전트 자율성 | 제한적 (도구 수준) | 완전한 자율성 |
| 보안 | 개별 구현 | 표준화된 보안 |
| 확장성 | 어려움 | 플러그 앤 플레이 |
| 벤더 종속성 | 높음 | 낮음 (표준 기반) |

## 🎯 핵심 이점

1. **상호운용성**: 다양한 벤더의 에이전트가 자유롭게 협업
2. **확장성**: 새로운 에이전트를 쉽게 추가
3. **유연성**: 다양한 사용 사례와 워크플로우 지원
4. **보안성**: 엔터프라이즈급 보안 기본 제공
5. **표준화**: 업계 표준으로 장기적 지원 보장

## 📚 참고 자료

- [A2A Protocol Specification](https://github.com/a2a-protocol/spec)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
- [OAuth 2.0 Framework](https://oauth.net/2/)
- [WebSocket Protocol](https://tools.ietf.org/html/rfc6455)