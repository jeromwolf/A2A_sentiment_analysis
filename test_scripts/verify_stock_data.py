#!/usr/bin/env python3
"""
주식 데이터 검증 스크립트
실제 데이터와 시스템 표시 데이터 비교
"""

import yfinance as yf
import pandas as pd
from datetime import datetime
import ta

def verify_aapl_data():
    print("🔍 AAPL 실시간 데이터 검증")
    print("=" * 50)
    
    # Yahoo Finance에서 데이터 가져오기
    stock = yf.Ticker("AAPL")
    
    # 1. 현재가 정보
    info = stock.info
    current_price = info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))
    previous_close = info.get('previousClose', info.get('regularMarketPreviousClose', 'N/A'))
    
    print(f"📊 가격 정보:")
    print(f"   현재가: ${current_price}")
    print(f"   전일 종가: ${previous_close}")
    
    if current_price != 'N/A' and previous_close != 'N/A':
        change_percent = ((current_price - previous_close) / previous_close) * 100
        print(f"   일일 변동률: {change_percent:.2f}%")
    
    # 2. 기술적 지표 계산
    print(f"\n📈 기술적 지표:")
    
    # 최근 30일 데이터로 RSI 계산
    hist = stock.history(period="1mo")
    if not hist.empty:
        # RSI 계산
        rsi = ta.momentum.RSIIndicator(close=hist['Close'], window=14)
        current_rsi = rsi.rsi().iloc[-1]
        print(f"   RSI (14일): {current_rsi:.1f}")
        
        # MACD 계산
        macd = ta.trend.MACD(close=hist['Close'])
        macd_line = macd.macd().iloc[-1]
        signal_line = macd.macd_signal().iloc[-1]
        macd_diff = macd_line - signal_line
        
        if macd_diff > 0:
            macd_signal = "bullish"
        elif macd_diff < 0:
            macd_signal = "bearish"
        else:
            macd_signal = "neutral"
            
        print(f"   MACD 신호: {macd_signal}")
        print(f"   MACD 값: {macd_line:.2f}")
        print(f"   Signal 값: {signal_line:.2f}")
    
    # 3. 추가 지표
    print(f"\n📊 추가 정보:")
    print(f"   시가총액: ${info.get('marketCap', 'N/A'):,}")
    print(f"   PE Ratio: {info.get('trailingPE', 'N/A')}")
    print(f"   52주 최고가: ${info.get('fiftyTwoWeekHigh', 'N/A')}")
    print(f"   52주 최저가: ${info.get('fiftyTwoWeekLow', 'N/A')}")
    
    print("\n✅ 위 데이터를 시스템 표시 값과 비교해보세요!")
    print("   - 현재가: $210.02 vs 실제")
    print("   - 변동률: -0.07% vs 실제")
    print("   - RSI: 50.0 vs 실제")
    print("   - MACD: neutral vs 실제")

if __name__ == "__main__":
    verify_aapl_data()