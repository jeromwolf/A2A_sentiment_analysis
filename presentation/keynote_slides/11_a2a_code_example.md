# 슬라이드 11: A2A 코드 예제

## A2A 통신 예시

### 에이전트 정의
```python
class SentimentAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Sentiment Agent",
            port=8202
        )
```

### 메시지 전송
```python
# 감성 분석 요청
await self.send_message(
    recipient="sentiment-agent",
    action="analyze",
    payload={
        "ticker": "AAPL",
        "data": collected_data
    }
)
```

### 메시지 처리
```python
async def handle_message(self, message: A2AMessage):
    if message.body.get("action") == "analyze":
        result = await self.analyze_sentiment(
            message.body.get("payload")
        )
        await self.reply_to_message(
            message, result
        )
```