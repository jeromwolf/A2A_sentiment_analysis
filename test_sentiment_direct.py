#!/usr/bin/env python3
"""
Direct test of the sentiment analysis agent V2
"""

import httpx
import asyncio
import json
from a2a_core.protocols.message import A2AMessage, MessageType

async def test_sentiment_agent():
    """Test sentiment analysis agent directly"""
    
    # Create test message
    message = A2AMessage.create_request(
        sender_id="test-sender",
        receiver_id="8779b351-5495-43f0-8ca7-7d2dc8839976",
        action="analyze_sentiment",
        payload={
            "ticker": "AAPL",
            "data": {
                "sec": [{
                    "form_type": "Filing",
                    "title": "최신 내부자 거래(Form 4) 공시가 확인되었으나, 거래 유형(매수/매도)을 특정할 수 없습니다.",
                    "filing_date": "2025-07-01",
                    "url": "http://example.com",
                    "content": "Apple Inc. insider trading activity reported."
                }]
            }
        }
    )
    
    # Send to sentiment agent
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8202/message",
            json=message.to_dict()
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Message sent successfully!")
        else:
            print("❌ Failed to send message")

if __name__ == "__main__":
    asyncio.run(test_sentiment_agent())