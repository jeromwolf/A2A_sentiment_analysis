#!/bin/bash

# Marp을 사용해서 프레젠테이션 파일 변환

echo "🎯 Marp 프레젠테이션 변환 시작..."

# HTML 버전 (브라우저에서 바로 볼 수 있음)
marp marp_presentation.md -o presentation.html
echo "✅ HTML 생성 완료: presentation.html"

# PDF 버전
marp marp_presentation.md --pdf -o presentation.pdf
echo "✅ PDF 생성 완료: presentation.pdf"

# PPTX 버전 (키노트에서 열기 가능)
marp marp_presentation.md --pptx -o presentation.pptx
echo "✅ PPTX 생성 완료: presentation.pptx"

echo ""
echo "📁 생성된 파일들:"
ls -la presentation.*

echo ""
echo "💡 사용 방법:"
echo "1. presentation.html - 브라우저에서 바로 열기"
echo "2. presentation.pdf - PDF 뷰어에서 열기"
echo "3. presentation.pptx - 키노트에서 열기 (파일 > 열기)"