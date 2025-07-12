#!/usr/bin/env python3
"""
A2A 감성 분석 시스템 아키텍처 다이어그램 생성 스크립트
Mermaid 다이어그램을 이미지 파일로 변환
"""

import os
import subprocess
import tempfile
from pathlib import Path

# Mermaid 다이어그램 정의
SYSTEM_ARCHITECTURE = """
graph TB
    subgraph "Client Layer"
        UI[Web UI<br/>http://localhost:8100]
    end
    
    subgraph "A2A Protocol Layer"
        WS[WebSocket Server<br/>Main Orchestrator V2<br/>:8100]
        REG[Registry Server<br/>:8001]
    end
    
    subgraph "Agent Layer - Data Collection"
        NLU[NLU Agent<br/>:8108<br/>티커 추출]
        NEWS[News Agent<br/>:8307<br/>Finnhub API]
        TWITTER[Twitter Agent<br/>:8209<br/>Twitter API v2]
        SEC[SEC Agent<br/>:8210<br/>SEC EDGAR]
    end
    
    subgraph "Agent Layer - Analysis"
        SENT[Sentiment Analysis Agent<br/>:8202<br/>Gemini/OpenAI/Ollama]
        QUANT[Quantitative Analysis Agent<br/>:8211<br/>yfinance/TA-Lib]
        SCORE[Score Calculation Agent<br/>:8203<br/>가중치 계산]
        RISK[Risk Analysis Agent<br/>:8212<br/>종합 리스크 평가]
    end
    
    subgraph "Agent Layer - Output"
        REPORT[Report Generation Agent<br/>:8204<br/>HTML/PDF 생성]
    end
    
    subgraph "External APIs"
        GEMINI[Google Gemini API]
        OPENAI[OpenAI API]
        FINNHUB[Finnhub API]
        TWITTER_API[Twitter API]
        SEC_API[SEC EDGAR API]
        YFINANCE[Yahoo Finance]
    end
    
    subgraph "Optional Services"
        REDIS[Redis Cache<br/>:6379]
    end
    
    %% Client to Orchestrator
    UI -.->|WebSocket| WS
    
    %% Registry connections
    WS -.->|Agent Discovery| REG
    NLU -.->|Register| REG
    NEWS -.->|Register| REG
    TWITTER -.->|Register| REG
    SEC -.->|Register| REG
    SENT -.->|Register| REG
    QUANT -.->|Register| REG
    SCORE -.->|Register| REG
    RISK -.->|Register| REG
    REPORT -.->|Register| REG
    
    %% Orchestration Flow
    WS -->|1. Extract Ticker| NLU
    NLU -->|Ticker Symbol| WS
    
    WS -->|2. Parallel Requests| NEWS
    WS -->|2. Parallel Requests| TWITTER
    WS -->|2. Parallel Requests| SEC
    WS -->|2. Parallel Requests| QUANT
    
    NEWS -->|News Data| WS
    TWITTER -->|Tweet Data| WS
    SEC -->|Filing Data| WS
    QUANT -->|Price Data| WS
    
    WS -->|3. Analyze Sentiment| SENT
    SENT -->|Sentiment Scores| WS
    
    WS -->|4. Calculate Score| SCORE
    SCORE -->|Weighted Score| WS
    
    WS -->|5. Analyze Risk| RISK
    RISK -->|Risk Assessment| WS
    
    WS -->|6. Generate Report| REPORT
    REPORT -->|Final Report| WS
    
    %% External API connections
    NLU -.->|LLM Query| GEMINI
    NEWS -.->|News Query| FINNHUB
    TWITTER -.->|Tweet Query| TWITTER_API
    SEC -.->|Filing Query| SEC_API
    SENT -.->|LLM Analysis| GEMINI
    SENT -.->|LLM Analysis| OPENAI
    QUANT -.->|Stock Data| YFINANCE
    RISK -.->|LLM Analysis| GEMINI
    REPORT -.->|LLM Generation| GEMINI
    
    %% Cache connections
    NLU -.->|Cache| REDIS
    NEWS -.->|Cache| REDIS
    TWITTER -.->|Cache| REDIS
    SEC -.->|Cache| REDIS
    SENT -.->|Cache| REDIS
    
    classDef client fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef orchestrator fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef collector fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef analyzer fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    classDef output fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef external fill:#f5f5f5,stroke:#424242,stroke-width:1px,stroke-dasharray: 5 5
    classDef optional fill:#efebe9,stroke:#3e2723,stroke-width:1px,stroke-dasharray: 5 5
    
    class UI client
    class WS,REG orchestrator
    class NLU,NEWS,TWITTER,SEC collector
    class SENT,QUANT,SCORE,RISK analyzer
    class REPORT output
    class GEMINI,OPENAI,FINNHUB,TWITTER_API,SEC_API,YFINANCE external
    class REDIS optional
"""

SEQUENCE_DIAGRAM = """
sequenceDiagram
    participant User
    participant UI as Web UI
    participant WS as WebSocket<br/>Orchestrator
    participant REG as Registry
    participant NLU as NLU Agent
    participant DC as Data Collectors<br/>(News/Twitter/SEC)
    participant QUANT as Quantitative<br/>Agent
    participant SENT as Sentiment<br/>Agent
    participant SCORE as Score<br/>Agent
    participant RISK as Risk<br/>Agent
    participant REPORT as Report<br/>Agent
    
    User->>UI: "애플 주가 어때?"
    UI->>WS: WebSocket 연결
    
    Note over WS,REG: Agent Discovery
    WS->>REG: Get available agents
    REG-->>WS: Agent list & endpoints
    
    Note over WS,NLU: 1. Ticker Extraction
    WS->>NLU: {"query": "애플 주가 어때?"}
    NLU->>NLU: LLM으로 티커 추출
    NLU-->>WS: {"ticker": "AAPL", "company": "Apple Inc."}
    
    Note over WS,QUANT: 2. Parallel Data Collection
    par News Collection
        WS->>DC: Get news for AAPL
        DC-->>WS: News articles
    and Twitter Collection
        WS->>DC: Get tweets for AAPL
        DC-->>WS: Tweet data
    and SEC Collection
        WS->>DC: Get SEC filings for AAPL
        DC-->>WS: Filing data
    and Price Analysis
        WS->>QUANT: Get price analysis for AAPL
        QUANT-->>WS: Technical indicators
    end
    
    Note over WS,SENT: 3. Sentiment Analysis
    WS->>SENT: Analyze all collected data
    SENT->>SENT: LLM 감성 분석
    SENT-->>WS: Sentiment scores by source
    
    Note over WS,SCORE: 4. Score Calculation
    WS->>SCORE: Calculate weighted score
    SCORE->>SCORE: Apply source weights
    SCORE-->>WS: Final investment score
    
    Note over WS,RISK: 5. Risk Analysis
    WS->>RISK: Comprehensive risk assessment
    RISK->>RISK: LLM 리스크 분석
    RISK-->>WS: Risk factors & mitigation
    
    Note over WS,REPORT: 6. Report Generation
    WS->>REPORT: Generate final report
    REPORT->>REPORT: Create HTML/PDF
    REPORT-->>WS: Complete report
    
    WS-->>UI: Stream results
    UI-->>User: Display analysis
"""

def check_mermaid_cli():
    """Mermaid CLI 설치 확인"""
    try:
        result = subprocess.run(['mmdc', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def install_mermaid_cli():
    """Mermaid CLI 설치 안내"""
    print("Mermaid CLI가 설치되어 있지 않습니다.")
    print("\n설치 방법:")
    print("1. Node.js가 설치되어 있는지 확인하세요")
    print("2. 다음 명령어로 설치하세요:")
    print("   npm install -g @mermaid-js/mermaid-cli")
    print("\n또는 Homebrew를 사용하는 경우:")
    print("   brew install mermaid-cli")
    return False

def generate_diagram(mermaid_code, output_file, title=""):
    """Mermaid 다이어그램을 이미지로 변환"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as f:
        f.write(mermaid_code)
        temp_file = f.name
    
    try:
        # Mermaid CLI로 이미지 생성
        cmd = [
            'mmdc',
            '-i', temp_file,
            '-o', output_file,
            '-t', 'default',
            '-b', 'white',
            '--width', '2400',
            '--height', '1800'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {title} 생성 완료: {output_file}")
            return True
        else:
            print(f"❌ {title} 생성 실패: {result.stderr}")
            return False
            
    finally:
        # 임시 파일 삭제
        if os.path.exists(temp_file):
            os.unlink(temp_file)

def generate_html_viewer():
    """Mermaid 다이어그램을 볼 수 있는 HTML 뷰어 생성"""
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>A2A 감성 분석 시스템 아키텍처</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1, h2 {{
            color: #333;
            margin-bottom: 20px;
        }}
        .diagram-container {{
            background-color: #fafafa;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            overflow-x: auto;
        }}
        .mermaid {{
            text-align: center;
        }}
        .description {{
            background-color: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 15px;
            margin: 20px 0;
        }}
        .legend {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin: 20px 0;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 4px;
            border: 1px solid #ccc;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 A2A 감성 분석 시스템 아키텍처</h1>
        
        <div class="description">
            <strong>시스템 개요:</strong> Agent-to-Agent 프로토콜 기반의 분산형 투자 분석 시스템으로, 
            여러 전문화된 AI 에이전트가 협업하여 종합적인 투자 분석을 제공합니다.
        </div>

        <h2>📊 시스템 전체 구조도</h2>
        <div class="diagram-container">
            <div class="mermaid">
{SYSTEM_ARCHITECTURE}
            </div>
        </div>

        <h2>🔄 데이터 처리 흐름</h2>
        <div class="diagram-container">
            <div class="mermaid">
{SEQUENCE_DIAGRAM}
            </div>
        </div>

        <h2>📋 범례</h2>
        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background-color: #e1f5fe;"></div>
                <span>Client Layer</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #f3e5f5;"></div>
                <span>Orchestrator</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #fff3e0;"></div>
                <span>Data Collection</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #e8f5e9;"></div>
                <span>Analysis</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #fce4ec;"></div>
                <span>Output</span>
            </div>
        </div>

        <h2>🔧 주요 포트 정보</h2>
        <ul>
            <li><strong>8001</strong>: Registry Server</li>
            <li><strong>8100</strong>: Main Orchestrator & Web UI</li>
            <li><strong>8108</strong>: NLU Agent</li>
            <li><strong>8307</strong>: News Agent</li>
            <li><strong>8209</strong>: Twitter Agent</li>
            <li><strong>8210</strong>: SEC Agent</li>
            <li><strong>8202</strong>: Sentiment Analysis Agent</li>
            <li><strong>8211</strong>: Quantitative Analysis Agent</li>
            <li><strong>8203</strong>: Score Calculation Agent</li>
            <li><strong>8212</strong>: Risk Analysis Agent</li>
            <li><strong>8204</strong>: Report Generation Agent</li>
        </ul>
    </div>

    <script>
        mermaid.initialize({{ 
            startOnLoad: true,
            theme: 'default',
            themeVariables: {{
                primaryColor: '#f3e5f5',
                primaryTextColor: '#333',
                primaryBorderColor: '#4a148c',
                lineColor: '#666',
                secondaryColor: '#e8f5e9',
                tertiaryColor: '#fff3e0'
            }}
        }});
    </script>
</body>
</html>"""
    
    output_file = "architecture_diagram.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTML 뷰어 생성 완료: {output_file}")
    print(f"   브라우저에서 열어보세요: file://{os.path.abspath(output_file)}")

def main():
    print("🚀 A2A 시스템 아키텍처 다이어그램 생성 중...")
    
    # Mermaid CLI 확인
    if check_mermaid_cli():
        print("✅ Mermaid CLI 감지됨")
        
        # PNG 이미지 생성
        generate_diagram(SYSTEM_ARCHITECTURE, "system_architecture.png", "시스템 아키텍처")
        generate_diagram(SEQUENCE_DIAGRAM, "sequence_diagram.png", "시퀀스 다이어그램")
        
        print("\n📁 생성된 파일:")
        print("   - system_architecture.png")
        print("   - sequence_diagram.png")
    else:
        print("⚠️  Mermaid CLI를 사용할 수 없습니다.")
        install_mermaid_cli()
    
    # HTML 뷰어는 항상 생성
    print("\n📄 HTML 뷰어 생성 중...")
    generate_html_viewer()
    
    print("\n✅ 완료!")

if __name__ == "__main__":
    main()