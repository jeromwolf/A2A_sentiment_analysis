# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is an Agent-to-Agent (A2A) sentiment analysis system for investment analysis. Multiple specialized AI agents collaborate to analyze user queries about stocks, collect data from multiple sources (news, Twitter, SEC filings), perform sentiment analysis, calculate weighted scores, and generate comprehensive reports.

### Core Architecture Flow
1. **Main Orchestrator** (`main_orchestrator_v2.py`): A2A protocol-based WebSocket server on port 8100 that coordinates all agents
2. **NLU Agent**: Extracts ticker symbols from natural language queries
3. **Data Collection Agents** (parallel execution):
   - News Agent (`news_agent_v2_pure.py`)
   - Twitter Agent (`twitter_agent_v2_pure.py`)
   - SEC Agent (`sec_agent_v2_pure.py`)
4. **Sentiment Analysis Agent**: Analyzes collected data using Gemini AI
5. **Quantitative Analysis Agent**: Analyzes price data and technical indicators
6. **Score Calculation Agent**: Applies source-based weights to calculate final scores
7. **Risk Analysis Agent**: Comprehensive risk assessment
8. **Report Generation Agent**: Creates final investment reports

### Agent Ports
- Registry Server: 8001
- Main Orchestrator: 8100
- NLU Agent: 8108
- News Agent: 8307
- Twitter Agent: 8209
- SEC Agent: 8210
- Sentiment Analysis: 8202
- Quantitative Analysis: 8211
- Score Calculation: 8203
- Risk Analysis: 8212
- Report Generation: 8204

## Key Commands

### Development & Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Start all services
chmod +x start_all.sh  # First time only
./start_all.sh

# Stop all services
chmod +x stop_all.sh  # First time only
./stop_all.sh

# Test individual agent (example)
uvicorn agents.nlu_agent_v2:app --port 8108 --reload

# Check running processes
ps aux | grep uvicorn

# View logs
# Services run in background, use system logs or add logging to files
```

### API Testing
```bash
# Test NLU agent
curl -X POST http://localhost:8108/extract_ticker -H "Content-Type: application/json" -d '{"query": "애플 주가 어때?"}'

# Access UI
open http://localhost:8100
```

## Critical Configuration

### Environment Variables (.env)
Required API keys must be configured in `.env` file:
- `GEMINI_API_KEY`: Google AI Studio API key for Gemini
- `FINNHUB_API_KEY`: Finnhub API key for news data
- `TWITTER_BEARER_TOKEN`: Twitter API v2 bearer token
- `SEC_API_USER_AGENT`: Format: "Name email@example.com"
- `MAX_ARTICLES_TO_SCRAPE`: Number of articles to analyze (default: 3)

### Source Weights
Defined in `agents/score_calculation_agent_v2.py`:
- 기업 공시 (SEC): 1.5
- 뉴스 (News): 1.0  
- 트위터 (Twitter): 0.7

## Important Notes

- All agents use FastAPI and run as separate microservices
- Communication between agents is via HTTP REST APIs
- WebSocket is used for real-time UI updates
- Agents process data in parallel where possible for performance
- The system uses weighted scoring based on data source reliability
- Gemini AI is used for natural language processing and report generation