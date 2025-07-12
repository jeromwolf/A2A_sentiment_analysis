from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("A2A_API_KEY", "default-api-key-change-me")
print(f"[AUTH] Loaded API_KEY: {API_KEY[:10]}... (length: {len(API_KEY)})")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    print(f"[AUTH] Verifying API key: {api_key[:10] if api_key else 'None'}... against {API_KEY[:10]}...")
    if api_key != API_KEY:
        print(f"[AUTH] API key mismatch! Received: '{api_key}', Expected: '{API_KEY}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return api_key