# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is an Agent-to-Agent (A2A) sentiment analysis system for investment analysis. Multiple specialized AI agents collaborate to analyze user queries about stocks, collect data from multiple sources (news, Twitter, SEC filings), perform sentiment analysis, calculate weighted scores, and generate comprehensive reports.

### Core Architecture Flow
1. **Main Orchestrator** (`main_orchestrator.py`): WebSocket server on port 8000 that coordinates all agents
2. **NLU Agent**: Extracts ticker symbols from natural language queries
3. **Data Collection Agents** (parallel execution):
   - News Agent (uses `advanced_data_agent.py`)
   - Twitter Agent
   - SEC Agent
4. **Sentiment Analysis Agent**: Analyzes collected data using Gemini AI
5. **Score Calculation Agent**: Applies source-based weights to calculate final scores
6. **Report Generation Agent**: Creates final investment reports

### Agent Ports
- Main Orchestrator: 8000
- NLU Agent: 8008
- News Agent: 8007
- Twitter Agent: 8009
- SEC Agent: 8010
- Sentiment Analysis: 8002
- Score Calculation: 8003
- Report Generation: 8004

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
uvicorn agents.nlu_agent:app --port 8008 --reload

# Check running processes
ps aux | grep uvicorn

# View logs
# Services run in background, use system logs or add logging to files
```

### API Testing
```bash
# Test NLU agent
curl -X POST http://localhost:8008/extract_ticker -H "Content-Type: application/json" -d '{"query": "애플 주가 어때?"}'

# Access UI
open http://localhost:8000
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
Defined in `agents/score_calculation_agent.py`:
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