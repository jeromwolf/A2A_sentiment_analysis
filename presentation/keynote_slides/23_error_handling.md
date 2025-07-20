# 슬라이드 23: 에러 처리

## 장애 대응: Fallback 메커니즘

### 3단계 에러 처리

#### 1️⃣ A2A 통신 시도
```python
success = await self.send_message(
    recipient="news-agent",
    action="collect_data"
)
```

#### 2️⃣ 실패 시 HTTP 직접 호출
```python
if not success:
    response = await http_client.post(
        "http://localhost:8307/collect_news_data",
        json={"ticker": ticker}
    )
```

#### 3️⃣ 그래도 실패 시 기본값
```python
if response.status_code != 200:
    return {"data": [], "error": "Service unavailable"}
```

### 장점
- ✅ 서비스 연속성 보장
- ✅ 부분 실패 허용
- ✅ 우아한 성능 저하