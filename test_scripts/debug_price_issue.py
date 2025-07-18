#!/usr/bin/env python3
"""
Debug script to trace where AAPL price $208.62 is being overwritten with $195.00
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import logging
from dotenv import load_dotenv

# Load environment
load_dotenv()

from agents.quantitative_agent_v2 import QuantitativeAgentV2
from agents.twelve_data_client import TwelveDataClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_aapl_price_sources():
    """Test all AAPL price sources to find where $195.00 comes from"""
    
    print("🔍 Debugging AAPL Price Sources")
    print("="*50)
    
    # 1. Test Twelve Data API directly
    print("\n1. Testing Twelve Data API directly...")
    twelve_data_api_key = os.getenv('TWELVE_DATA_API_KEY')
    if twelve_data_api_key:
        client = TwelveDataClient(twelve_data_api_key)
        quote_data = client.get_quote('AAPL')
        if quote_data:
            print(f"   ✅ Twelve Data AAPL Close: ${quote_data.get('close', 'N/A')}")
            print(f"   📊 Full quote data: {quote_data}")
        else:
            print("   ❌ Twelve Data failed")
    else:
        print("   ⚠️ No Twelve Data API key")
    
    # 2. Test Yahoo Finance
    print("\n2. Testing Yahoo Finance...")
    try:
        import yfinance as yf
        stock = yf.Ticker('AAPL')
        hist = stock.history(period="1d")
        if not hist.empty:
            current_price = float(hist['Close'].iloc[-1])
            print(f"   ✅ Yahoo Finance AAPL Close: ${current_price}")
        else:
            print("   ❌ Yahoo Finance failed - no data")
    except Exception as e:
        print(f"   ❌ Yahoo Finance failed: {e}")
    
    # 3. Test QuantitativeAgent analysis flow
    print("\n3. Testing QuantitativeAgent analysis flow...")
    agent = QuantitativeAgentV2()
    
    # Check if mock data is enabled
    print(f"   Mock data enabled: {agent.use_mock_data}")
    print(f"   USE_MOCK_DATA env: {os.getenv('USE_MOCK_DATA')}")
    
    # Run the analysis
    try:
        result = await agent._analyze_quantitative_data('AAPL', '1mo')
        price_data = result.get('price_data', {})
        current_price = price_data.get('current', 'N/A')
        print(f"   📊 QuantitativeAgent AAPL Current: ${current_price}")
        
        # Check which data source was used
        if 'error' in result:
            print(f"   ❌ Error: {result['error']}")
        else:
            print(f"   ✅ Analysis completed")
            print(f"   📈 Price data keys: {list(price_data.keys())}")
            
    except Exception as e:
        print(f"   ❌ QuantitativeAgent failed: {e}")
        import traceback
        traceback.print_exc()
    
    # 4. Check mock data values
    print("\n4. Checking mock data values...")
    mock_data = agent._get_mock_data('AAPL')
    mock_price = mock_data.get('price_data', {}).get('current_price', 'N/A')
    print(f"   🎭 Mock data AAPL price: ${mock_price}")
    
    print("\n" + "="*50)
    print("🔍 Debug complete!")

if __name__ == "__main__":
    asyncio.run(test_aapl_price_sources())