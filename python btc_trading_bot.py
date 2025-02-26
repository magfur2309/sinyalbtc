import requests
import pandas as pd
import pandas_ta as ta
import time
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler

# API Binance untuk harga BTC/USDT
BINANCE_API_URL = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=100"

# API Telegram untuk notifikasi
TELEGRAM_TOKEN = "7692585926:AAF0Wxcaco0-tc5n_n41oe6lKUB-bEg4-ic"  # Ganti dengan token bot Telegram
TELEGRAM_CHAT_ID = "t.me/ngepirbot"  # Ganti dengan chat ID Telegram

def send_telegram_message(message):
    """Mengirim pesan ke Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, data=data)

def get_btc_prices():
    """Mengambil data harga candle terakhir dari Binance (1 menit)"""
    try:
        response = requests.get(BINANCE_API_URL)
        data = response.json()
        df = pd.DataFrame(data, columns=["Time", "Open", "High", "Low", "Close", "Volume", "_", "_", "_", "_", "_", "_"])
        df = df.astype(float)
        return df
    except Exception as e:
        print("Error:", e)
        return None

def detect_candlestick_patterns(df):
    """Mendeteksi pola candlestick utama"""
    df["Hammer"] = ta.cdl_hammer(df["Open"], df["High"], df["Low"], df["Close"])
    df["Engulfing"] = ta.cdl_engulfing(df["Open"], df["High"], df["Low"], df["Close"])
    df["Shooting Star"] = ta.cdl_shootingstar(df["Open"], df["High"], df["Low"], df["Close"])
    
    patterns = []
    if df["Hammer"].iloc[-1] > 0:
        patterns.append("📈 Hammer (Bullish)")
    if df["Engulfing"].iloc[-1] > 0:
        patterns.append("📈 Bullish Engulfing")
    if df["Engulfing"].iloc[-1] < 0:
        patterns.append("📉 Bearish Engulfing")
    if df["Shooting Star"].iloc[-1] > 0:
        patterns.append("📉 Shooting Star (Bearish)")
    
    return patterns

while True:
    df = get_btc_prices()
    
    if df is not None:
        df["RSI"] = ta.rsi(df["Close"], length=14)
        macd = df.ta.macd(fast=12, slow=26, signal=9)
        df["MACD"] = macd["MACD_12_26_9"]
        df["Signal"] = macd["MACDs_12_26_9"]
        
        # Harga terbaru & indikator
        current_price = df["Close"].iloc[-1]
        latest_rsi = df["RSI"].iloc[-1]
        latest_macd = df["MACD"].iloc[-1]
        latest_signal = df["Signal"].iloc[-1]
        
        # Deteksi pola candlestick
        patterns = detect_candlestick_patterns(df)
        
        # Menentukan sinyal beli/jual
        signal = "⏳ Tunggu..."
        telegram_message = None
        
        if latest_rsi < 30 and latest_macd > latest_signal:
            signal = "📈 Beli! (Oversold & MACD Bullish)"
        elif latest_rsi > 70 and latest_macd < latest_signal:
            signal = "📉 Jual! (Overbought & MACD Bearish)"
        
        # Print hasil analisis
        print(f"BTC/USDT: ${current_price}")
        print(f"RSI: {latest_rsi:.2f} | MACD: {latest_macd:.2f} | Signal: {latest_signal:.2f}")
        print(f"Pola Candlestick: {', '.join(patterns) if patterns else 'Tidak ada'}")
        print(f"📊 Sinyal: {signal}")
        print("-" * 40)
        
        # Kirim notifikasi Telegram jika ada sinyal penting
        if latest_rsi < 30 or latest_rsi > 70:
            telegram_message = f"⚡ BTC/USDT: ${current_price}\n📊 Sinyal: {signal}"
            send_telegram_message(telegram_message)
        
    time.sleep(60)
