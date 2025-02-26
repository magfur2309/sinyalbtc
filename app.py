import requests
import pandas as pd
import pandas_ta as ta
import time
import os
from dotenv import load_dotenv

# Load variabel lingkungan dari .env
load_dotenv()

# API Binance untuk harga BTC/USDT
BINANCE_API_URL = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=100"

# API Telegram untuk notifikasi (Gunakan variabel lingkungan)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(message):
    """Mengirim pesan ke Telegram dengan pengecekan error."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Token atau Chat ID Telegram tidak ditemukan!")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    
    try:
        response = requests.post(url, data=data, timeout=10)
        response.raise_for_status()  # Raise error jika request gagal
    except requests.RequestException as e:
        print(f"❌ Gagal mengirim pesan Telegram: {e}")

def get_btc_prices():
    """Mengambil data harga candle terakhir dari Binance (1 menit)"""
    try:
        response = requests.get(BINANCE_API_URL, timeout=10)
        response.raise_for_status()  # Raise error jika request gagal
        data = response.json()
        
        df = pd.DataFrame(data, columns=["Time", "Open", "High", "Low", "Close", "Volume", "_", "_", "_", "_", "_", "_"])
        df = df.astype(float)
        return df
    except requests.RequestException as e:
        print(f"❌ Gagal mengambil data dari Binance: {e}")
        return None

while True:
    df = get_btc_prices()
    
    if df is not None:
        df["RSI"] = df.ta.rsi(length=14)
        macd = df.ta.macd(fast=12, slow=26, signal=9)
        df["MACD"] = macd["MACD_12_26_9"]
        df["Signal"] = macd["MACDs_12_26_9"]
        
        # Harga terbaru & indikator
        current_price = df["Close"].iloc[-1]
        latest_rsi = df["RSI"].iloc[-1]
        latest_macd = df["MACD"].iloc[-1]
        latest_signal = df["Signal"].iloc[-1]
        
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
        print(f"📊 Sinyal: {signal}")
        print("-" * 40)
        
        # Kirim notifikasi Telegram jika ada sinyal penting
        if latest_rsi < 30 or latest_rsi > 70:
            telegram_message = f"⚡ BTC/USDT: ${current_price}\n📊 Sinyal: {signal}"
            send_telegram_message(telegram_message)
    
    time.sleep(60)
