#!/usr/bin/env python3
"""
A2A 시스템 아키텍처를 다양한 형식으로 시각화하는 스크립트
- 간단한 ASCII 아트
- Graphviz DOT 파일
- PlantUML 다이어그램
- Draw.io XML
"""

import json
from pathlib import Path

def create_ascii_architecture():
    """ASCII 아트로 시스템 구조 표현"""
    ascii_art = """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║                        A2A 감성 분석 시스템 아키텍처                           ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝

    ┌─────────────────────────────────────────────────────────────────────────────┐
    │                              사용자 인터페이스                               │
    │                         Web UI (http://localhost:8100)                       │
    └─────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼ WebSocket
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │                            중앙 오케스트레이터                               │
    │                    Main Orchestrator V2 (포트: 8100)                         │
    │                    Registry Server (포트: 8001)                              │
    └─────────────────────────────────────────────────────────────────────────────┘
                                          │
                ┌─────────────────────────┴─────────────────────────┐
                ▼                                                   ▼
    ┌───────────────────────────┐                    ┌──────────────────────────┐
    │    1단계: 티커 추출       │                    │   2단계: 데이터 수집     │
    │    NLU Agent (:8108)      │                    │                          │
    │    - 자연어 이해          │                    │  병렬 처리:              │
    │    - 티커 심볼 추출       │                    │  • News Agent (:8307)    │
    └───────────────────────────┘                    │  • Twitter Agent (:8209) │
                                                     │  • SEC Agent (:8210)     │
                                                     │  • Quant Agent (:8211)   │
                                                     └──────────────────────────┘
                                                                  │
                                                                  ▼
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │                            3-5단계: 분석 처리                                │
    │                                                                             │
    │  ┌─────────────────────┐  ┌─────────────────────┐  ┌──────────────────┐   │
    │  │ Sentiment Analysis  │  │  Score Calculation  │  │  Risk Analysis   │   │
    │  │  Agent (:8202)      │─▶│   Agent (:8203)     │─▶│  Agent (:8212)   │   │
    │  │ • 감성 분석         │  │ • 가중치 적용       │  │ • 리스크 평가    │   │
    │  │ • 다중 LLM 지원     │  │ • 종합 점수 계산    │  │ • 투자 권고      │   │
    │  └─────────────────────┘  └─────────────────────┘  └──────────────────┘   │
    └─────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │                           6단계: 리포트 생성                                  │
    │                     Report Generation Agent (:8204)                          │
    │                        • HTML/PDF 보고서 생성                                │
    └─────────────────────────────────────────────────────────────────────────────┘

    【외부 API 연동】
    • Gemini API (Google AI)    • OpenAI API       • Finnhub API
    • Twitter API v2            • SEC EDGAR API    • Yahoo Finance

    【데이터 소스 가중치】
    • SEC 공시: 1.5 (높음)      • 뉴스: 1.0 (보통)     • 트위터: 0.7 (낮음)
    """
    
    with open("architecture_ascii.txt", "w", encoding="utf-8") as f:
        f.write(ascii_art)
    
    print("✅ ASCII 아키텍처 다이어그램 생성: architecture_ascii.txt")
    return ascii_art

def create_graphviz_dot():
    """Graphviz DOT 형식으로 다이어그램 생성"""
    dot_content = """digraph A2A_Architecture {
    // 그래프 설정
    rankdir=TB;
    node [shape=box, style="rounded,filled", fontname="Arial"];
    edge [fontname="Arial"];
    
    // 색상 정의
    node [fillcolor="#e1f5fe"];
    
    // 노드 정의
    UI [label="Web UI\\n:8100", fillcolor="#e1f5fe"];
    Orchestrator [label="Main Orchestrator\\n& Registry Server\\n:8100 / :8001", fillcolor="#f3e5f5", shape=box3d];
    
    // 데이터 수집 에이전트
    NLU [label="NLU Agent\\n:8108\\n티커 추출", fillcolor="#fff3e0"];
    News [label="News Agent\\n:8307\\nFinnhub", fillcolor="#fff3e0"];
    Twitter [label="Twitter Agent\\n:8209\\nTwitter API", fillcolor="#fff3e0"];
    SEC [label="SEC Agent\\n:8210\\nEDGAR", fillcolor="#fff3e0"];
    
    // 분석 에이전트
    Sentiment [label="Sentiment Analysis\\n:8202\\n감성 분석", fillcolor="#e8f5e9"];
    Quant [label="Quantitative Analysis\\n:8211\\n기술적 분석", fillcolor="#e8f5e9"];
    Score [label="Score Calculation\\n:8203\\n점수 계산", fillcolor="#e8f5e9"];
    Risk [label="Risk Analysis\\n:8212\\n리스크 평가", fillcolor="#e8f5e9"];
    
    // 출력 에이전트
    Report [label="Report Generation\\n:8204\\nHTML/PDF", fillcolor="#fce4ec"];
    
    // 연결선
    UI -> Orchestrator [label="WebSocket"];
    Orchestrator -> NLU [label="1. 티커 추출"];
    
    Orchestrator -> News [label="2. 병렬 수집"];
    Orchestrator -> Twitter [label="2. 병렬 수집"];
    Orchestrator -> SEC [label="2. 병렬 수집"];
    Orchestrator -> Quant [label="2. 병렬 수집"];
    
    {News, Twitter, SEC} -> Sentiment [label="3. 데이터"];
    Quant -> Score [label="4. 기술 지표"];
    Sentiment -> Score [label="4. 감성 점수"];
    Score -> Risk [label="5. 종합 점수"];
    Risk -> Report [label="6. 분석 결과"];
    
    // 서브그래프로 그룹화
    subgraph cluster_collection {
        label="데이터 수집";
        style=filled;
        fillcolor="#fff8e1";
        News; Twitter; SEC;
    }
    
    subgraph cluster_analysis {
        label="분석 처리";
        style=filled;
        fillcolor="#e8f5e9";
        Sentiment; Quant; Score; Risk;
    }
}"""
    
    with open("architecture.dot", "w", encoding="utf-8") as f:
        f.write(dot_content)
    
    print("✅ Graphviz DOT 파일 생성: architecture.dot")
    print("   변환 명령어: dot -Tpng architecture.dot -o architecture_graphviz.png")
    return dot_content

def create_plantuml():
    """PlantUML 다이어그램 생성"""
    plantuml_content = """@startuml A2A_Architecture
!theme plain

title A2A 감성 분석 시스템 아키텍처

' 색상 정의
!define CLIENT_COLOR #e1f5fe
!define ORCHESTRATOR_COLOR #f3e5f5
!define COLLECTOR_COLOR #fff3e0
!define ANALYZER_COLOR #e8f5e9
!define OUTPUT_COLOR #fce4ec

' 컴포넌트 정의
package "클라이언트" <<CLIENT_COLOR>> {
    [Web UI :8100] as UI
}

package "오케스트레이터" <<ORCHESTRATOR_COLOR>> {
    [Main Orchestrator :8100] as MO
    [Registry Server :8001] as REG
}

package "데이터 수집" <<COLLECTOR_COLOR>> {
    [NLU Agent :8108] as NLU
    [News Agent :8307] as NEWS
    [Twitter Agent :8209] as TWITTER
    [SEC Agent :8210] as SEC
}

package "분석 처리" <<ANALYZER_COLOR>> {
    [Sentiment Analysis :8202] as SENT
    [Quantitative Analysis :8211] as QUANT
    [Score Calculation :8203] as SCORE
    [Risk Analysis :8212] as RISK
}

package "결과 생성" <<OUTPUT_COLOR>> {
    [Report Generation :8204] as REPORT
}

' 연결 관계
UI -down-> MO : WebSocket
MO <--> REG : 에이전트 등록

MO --> NLU : 1. 티커 추출
MO --> NEWS : 2. 뉴스 수집
MO --> TWITTER : 2. 트윗 수집
MO --> SEC : 2. 공시 수집
MO --> QUANT : 2. 주가 분석

NEWS --> SENT : 3. 데이터
TWITTER --> SENT : 3. 데이터
SEC --> SENT : 3. 데이터

SENT --> SCORE : 4. 감성 점수
QUANT --> SCORE : 4. 기술 지표

SCORE --> RISK : 5. 종합 점수
RISK --> REPORT : 6. 분석 결과

' 외부 API
database "외부 API" {
    [Gemini/OpenAI]
    [Finnhub]
    [Twitter API]
    [SEC EDGAR]
    [Yahoo Finance]
}

@enduml"""
    
    with open("architecture.puml", "w", encoding="utf-8") as f:
        f.write(plantuml_content)
    
    print("✅ PlantUML 파일 생성: architecture.puml")
    print("   온라인 렌더링: https://www.plantuml.com/plantuml")
    return plantuml_content

def create_drawio_xml():
    """Draw.io (diagrams.net) XML 형식 생성"""
    drawio_template = """<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" modified="2024-01-01T00:00:00.000Z" agent="5.0" version="21.1.2" etag="v1" type="device">
  <diagram name="A2A Architecture" id="a2a">
    <mxGraphModel dx="1400" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1600" pageHeight="1200" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        
        <!-- 사용자 인터페이스 -->
        <mxCell id="ui" value="Web UI&#xa;http://localhost:8100" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1f5fe;strokeColor=#01579b;" vertex="1" parent="1">
          <mxGeometry x="700" y="40" width="200" height="60" as="geometry" />
        </mxCell>
        
        <!-- 오케스트레이터 -->
        <mxCell id="orchestrator" value="Main Orchestrator V2&#xa;Registry Server&#xa;:8100 / :8001" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f3e5f5;strokeColor=#4a148c;strokeWidth=2;" vertex="1" parent="1">
          <mxGeometry x="650" y="150" width="300" height="80" as="geometry" />
        </mxCell>
        
        <!-- NLU Agent -->
        <mxCell id="nlu" value="NLU Agent&#xa;:8108&#xa;티커 추출" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff3e0;strokeColor=#e65100;" vertex="1" parent="1">
          <mxGeometry x="100" y="300" width="150" height="80" as="geometry" />
        </mxCell>
        
        <!-- 데이터 수집 에이전트들 -->
        <mxCell id="news" value="News Agent&#xa;:8307&#xa;Finnhub" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff3e0;strokeColor=#e65100;" vertex="1" parent="1">
          <mxGeometry x="300" y="300" width="150" height="80" as="geometry" />
        </mxCell>
        
        <mxCell id="twitter" value="Twitter Agent&#xa;:8209&#xa;Twitter API" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff3e0;strokeColor=#e65100;" vertex="1" parent="1">
          <mxGeometry x="500" y="300" width="150" height="80" as="geometry" />
        </mxCell>
        
        <mxCell id="sec" value="SEC Agent&#xa;:8210&#xa;SEC EDGAR" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff3e0;strokeColor=#e65100;" vertex="1" parent="1">
          <mxGeometry x="700" y="300" width="150" height="80" as="geometry" />
        </mxCell>
        
        <mxCell id="quant" value="Quantitative Agent&#xa;:8211&#xa;기술적 분석" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#1b5e20;" vertex="1" parent="1">
          <mxGeometry x="900" y="300" width="150" height="80" as="geometry" />
        </mxCell>
        
        <!-- 분석 에이전트들 -->
        <mxCell id="sentiment" value="Sentiment Analysis&#xa;:8202&#xa;감성 분석" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#1b5e20;" vertex="1" parent="1">
          <mxGeometry x="300" y="450" width="200" height="80" as="geometry" />
        </mxCell>
        
        <mxCell id="score" value="Score Calculation&#xa;:8203&#xa;점수 계산" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#1b5e20;" vertex="1" parent="1">
          <mxGeometry x="550" y="450" width="200" height="80" as="geometry" />
        </mxCell>
        
        <mxCell id="risk" value="Risk Analysis&#xa;:8212&#xa;리스크 평가" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#1b5e20;" vertex="1" parent="1">
          <mxGeometry x="800" y="450" width="200" height="80" as="geometry" />
        </mxCell>
        
        <!-- 리포트 생성 -->
        <mxCell id="report" value="Report Generation&#xa;:8204&#xa;HTML/PDF 생성" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fce4ec;strokeColor=#880e4f;" vertex="1" parent="1">
          <mxGeometry x="650" y="600" width="300" height="80" as="geometry" />
        </mxCell>
        
        <!-- 연결선들 -->
        <mxCell id="edge1" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;" edge="1" parent="1" source="ui" target="orchestrator">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>"""
    
    with open("architecture.drawio", "w", encoding="utf-8") as f:
        f.write(drawio_template)
    
    print("✅ Draw.io 파일 생성: architecture.drawio")
    print("   https://app.diagrams.net 에서 열어서 편집 가능")
    return drawio_template

def create_simple_table():
    """간단한 테이블 형식으로 정리"""
    table_content = """
# A2A 감성 분석 시스템 구성 요소

## 🏗️ 시스템 계층 구조

### 1️⃣ 클라이언트 계층
| 구성 요소 | 포트 | 역할 |
|----------|------|------|
| Web UI | 8100 | 사용자 인터페이스 |

### 2️⃣ 오케스트레이션 계층
| 구성 요소 | 포트 | 역할 |
|----------|------|------|
| Main Orchestrator | 8100 | 전체 워크플로우 조정 |
| Registry Server | 8001 | 에이전트 등록/발견 |

### 3️⃣ 데이터 수집 계층
| 에이전트 | 포트 | 역할 | 외부 API |
|---------|------|------|----------|
| NLU Agent | 8108 | 티커 심볼 추출 | Gemini AI |
| News Agent | 8307 | 뉴스 데이터 수집 | Finnhub |
| Twitter Agent | 8209 | 소셜 데이터 수집 | Twitter API v2 |
| SEC Agent | 8210 | 공시 자료 수집 | SEC EDGAR |

### 4️⃣ 분석 처리 계층
| 에이전트 | 포트 | 역할 | 가중치 |
|---------|------|------|--------|
| Sentiment Analysis | 8202 | 감성 분석 | - |
| Quantitative Analysis | 8211 | 기술적 분석 | - |
| Score Calculation | 8203 | 점수 계산 | SEC: 1.5, News: 1.0, Twitter: 0.7 |
| Risk Analysis | 8212 | 리스크 평가 | - |

### 5️⃣ 출력 계층
| 에이전트 | 포트 | 역할 |
|---------|------|------|
| Report Generation | 8204 | HTML/PDF 보고서 생성 |

## 📊 처리 흐름

1. **사용자 입력** → Web UI
2. **티커 추출** → NLU Agent가 자연어에서 주식 심볼 추출
3. **데이터 수집** → 4개 에이전트가 병렬로 데이터 수집
4. **감성 분석** → 수집된 데이터를 AI로 분석
5. **점수 계산** → 소스별 가중치 적용하여 종합 점수 산출
6. **리스크 평가** → 투자 리스크 분석
7. **보고서 생성** → 최종 투자 분석 보고서 작성

## 🔗 주요 특징

- **병렬 처리**: 데이터 수집 단계에서 모든 에이전트가 동시 실행
- **가중치 시스템**: 데이터 소스의 신뢰도에 따른 차별화된 가중치
- **다중 LLM 지원**: OpenAI, Gemini, Ollama 선택 가능
- **실시간 업데이트**: WebSocket을 통한 진행 상황 실시간 전달
"""
    
    with open("architecture_table.md", "w", encoding="utf-8") as f:
        f.write(table_content)
    
    print("✅ 테이블 형식 문서 생성: architecture_table.md")
    return table_content

def main():
    """모든 형식의 다이어그램 생성"""
    print("🎨 A2A 시스템 아키텍처를 다양한 형식으로 생성합니다...\n")
    
    # 1. ASCII 아트
    create_ascii_architecture()
    
    # 2. Graphviz DOT
    create_graphviz_dot()
    
    # 3. PlantUML
    create_plantuml()
    
    # 4. Draw.io XML
    create_drawio_xml()
    
    # 5. 간단한 테이블
    create_simple_table()
    
    print("\n✅ 모든 형식의 다이어그램이 생성되었습니다!")
    print("\n📝 사용 방법:")
    print("1. ASCII: architecture_ascii.txt - 텍스트 에디터에서 바로 확인")
    print("2. Graphviz: architecture.dot - 'dot -Tpng architecture.dot -o output.png' 실행")
    print("3. PlantUML: architecture.puml - PlantUML 서버나 IDE 플러그인 사용")
    print("4. Draw.io: architecture.drawio - https://app.diagrams.net 에서 열기")
    print("5. 테이블: architecture_table.md - 마크다운 뷰어에서 확인")

if __name__ == "__main__":
    main()