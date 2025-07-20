---
marp: true
theme: default
paginate: true
---

# A2A 심화 이해 4: 고급 통신 패턴

## 우리 프로젝트의 실제 통신 플로우

### 1. 데이터 수집 병렬화 (메인 오케스트레이터)
```python
# 여러 에이전트에게 동시 요청
tasks = []
for agent in ["news-agent", "twitter-agent", "sec-agent", "mcp-agent"]:
    task = asyncio.create_task(
        self.send_message(
            recipient=agent,
            action="collect_data",
            payload={"ticker": "AAPL"}
        )
    )
    tasks.append(task)

# 모든 데이터 수집 완료 대기
results = await asyncio.gather(*tasks)
```

### 2. 분석 체인 (Sentiment → Score → Report)
```python
# 1. 감성 분석 요청
sentiment_result = await self.send_message(
    recipient="sentiment-agent",
    action="analyze",
    payload={"ticker": ticker, "data": collected_data}
)

# 2. 점수 계산 (가중치 적용)
score_result = await self.send_message(
    recipient="score-agent", 
    action="calculate_score",
    payload={"sentiment_data": sentiment_result}
)
```

### 3. 실시간 UI 업데이트 (WebSocket)
```python
# 진행 상황 브로드캐스트
await self.broadcast_event({
    "event": "analysis_progress",
    "status": "📰 NEWS 데이터 수집 완료: 5개 항목"
})
```

---