#!/bin/bash

# 현재 디렉토리 확인
echo "📁 현재 위치: $(pwd)"

# marp_slides 디렉토리로 이동
cd "$(dirname "$0")"

echo "🎯 PPTX 변환 시작..."

# PPTX로 변환
marp marp_presentation.md --pptx -o presentation.pptx

if [ $? -eq 0 ]; then
    echo "✅ PPTX 변환 완료!"
    echo "📄 생성된 파일: presentation.pptx"
    echo ""
    echo "💡 키노트에서 사용하기:"
    echo "1. 키노트 실행"
    echo "2. 파일 > 열기"
    echo "3. presentation.pptx 선택"
    echo "4. 편집 후 키노트 형식으로 저장"
else
    echo "❌ 변환 실패. Marp이 설치되어 있는지 확인하세요."
    echo "설치 명령: npm install -g @marp-team/marp-cli"
fi