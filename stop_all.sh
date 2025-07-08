#!/bin/bash
echo "🛑 V2 시스템을 종료합니다..."

# V2 포트 목록
V2_PORTS=(8001 8100 8108 8307 8209 8210 8202 8211 8212 8203 8204 8207 8208 8309 8310)

for port in "${V2_PORTS[@]}"; do
    echo "포트 $port 종료 중..."
    lsof -ti:$port | xargs kill -9 2>/dev/null
done

echo "✅ V2 시스템이 종료되었습니다."