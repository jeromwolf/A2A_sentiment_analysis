#!/usr/bin/env python3
import os
import httpx
import asyncio
from dotenv import load_dotenv
import json

load_dotenv()

async def test_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found")
        return
        
    print(f"✅ API Key found: {api_key[:10]}...")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{"text": "Say hello in Korean"}]
        }]
    }
    
    print(f"🚀 Sending request to Gemini API...")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            print(f"📥 Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success!")
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(f"❌ Error: {response.text}")
                
    except httpx.TimeoutException:
        print("⏱️ Request timed out after 30 seconds")
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_gemini())