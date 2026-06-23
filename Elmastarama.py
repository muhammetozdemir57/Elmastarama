import yfinance as yf
import pandas as pd
import pandas_ta as ta
import warnings
from bist_data import get_all_tickers  # BIST'teki tüm güncel hisseleri (510+) çeken kütüphane

# Gereksiz terminal uyarılarını gizle
warnings.filterwarnings('ignore')

print("1. Adım: Güncel BIST Hisse Listesi (510+ Şirket) Çekiliyor...")
try:
    # Tüm aktif BIST hisselerini çeker (Örn: ['THYAO', 'EUREN', 'ADEL', ...])
    raw_tickers = get_all_tickers()
    
    # Yahoo Finance için sonlarına '.IS' ekliyoruz ve sığ/fon olan varyantları temizliyoruz
    bist_tickers = [f"{ticker}.IS" for ticker in raw_tickers if not ticker.endswith(('F', 'BY', 'E'))]
    print(f"Başarılı! Toplam {len(bist_tickers)} aktif hisse senedi tarama listesine alındı.\n")
except Exception as e:
    print(f"Hisse listesi çekilemedi, varsayılan liste kullanılıyor. Hata: {e}")
    # Yedek acil durum listesi
    bist_tickers = ["THYAO.IS", "EUREN.IS", "ADEL.IS", "KOCMT.IS", "KOPOL.IS", "INFO.IS"]

found_stocks = []

print("2. Adım: 'Dip Elmas Oluşumu' Filtre Taraması Başlatılıyor...\n")

for index, ticker in enumerate(bist_tickers, 1):
    try:
        # İlerleme durumunu terminalde görmek için (Örn: 45/512)
        if index % 50 == 0 or index == len(bist_tickers):
            print(f"Tarama Durumu: {index}/{len(bist_tickers)} hisse kontrol edildi...")

        # 6 aylık veri tüm indikatörler için yeterlidir
        df = yf.download(ticker, period="6mo", progress=False)
        
        if df.empty or len(df) < 100:
            continue
            
        # yfinance multi-index sütun temizliği
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)

        close = df['Close']
        volume = df['Volume']
        high = df['High']
        low = df['Low']
        
        # İndikatör Hesaplamaları
        ema20 = ta.ema(close, length=20)
        sma100 = ta.sma(close, length=100)
        rsi14 = ta.rsi(close, length=14)
        adx14 = ta.adx(high, low, close, length=14)['ADX_14']
        
        macd = ta.macd(close, fast=12, slow=26, signal=9)
        macd_line = macd['MACD_12_26_9']
        signal_line = macd['MACDs_12_26_9']
        
        vol_sma10 = ta.sma(volume, length=10)
        vol_sma30 = ta.sma(volume, length=30)
        
        # 10 Maddelik Strateji Koşulları (Son günün kapanış verilerine göre)
        cond1 = close.iloc[-1] > ema20.iloc[-1]
        
        perf3m = ((close.iloc[-1] - close.iloc[-64]) / close.iloc[-64]) * 100 if len(close) > 64 else 0
        cond2 = perf3m < 0
        
        cond3 = adx14.iloc[-1] < 25
        
        rel_vol = volume.iloc[-1] / vol_sma10.iloc[-1] if vol_sma10.iloc[-1] > 0 else 0
        cond4 = rel_vol > 1.2
        
        cond5 = volume.iloc[-1] > vol_sma10.iloc[-1]
        cond6 = vol_sma10.iloc[-1] > vol_sma30.iloc[-1]
        cond7 = 45 <= rsi14.iloc[-1] <= 65
        cond8 = macd_line.iloc[-1] > signal_line.iloc[-1]
        
        perf1m = ((close.iloc[-1] - close.iloc[-22]) / close.iloc[-22]) * 100 if len(close) > 22 else 0
        cond9 = perf1m > 0
        
        cond10 = close.iloc[-1] < sma100.iloc[-1]
        
        # Tüm koşulların kontrolü
        if all([cond1, cond2, cond3, cond4, cond5, cond6, cond7, cond8, cond9, cond10]):
            clean_name = ticker.replace('.IS', '')
            found_stocks.append(clean_name)
            print(f" ✨ SİNYAL YAKALANDI: {clean_name}")
            
    except Exception:
        # Hatalı veya borsadan geçici olarak uzaklaştırılan hisseleri sessizce atla
        pass

print("\n" + "="*40)
print("🎯 510+ HİSSE TARAMA SONUÇLARI 🎯")
print("="*40)
if found_stocks:
    print(f"Bugün Elmas Formasyonu Şartlarını Sağlayan Hisseler:\n👉 {', '.join(found_stocks)}")
else:
    print("Bugün 10/10 şartı sağlayan herhangi bir BIST hissesi bulunamadı.")
print("="*40)
