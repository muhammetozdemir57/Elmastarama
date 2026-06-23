import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import warnings
from bist_data import get_all_tickers

warnings.filterwarnings('ignore')

# Sayfa Yapılandırması
st.set_page_config(page_title="BIST Dip Elmas Tarayıcı", page_icon="💎", layout="wide")

st.title("💎 BIST - Dip Elmas Oluşumu Tarayıcısı")
st.write("Bu sistem, Borsa İstanbul'daki 510+ hisseyi 10 farklı teknik analiz kriterine göre canlı olarak tarar.")

# Tarama Butonu
if st.button("Taramayı Başlat (Canlı Veri)", type="primary"):
    
    with st.spinner("Güncel BIST Hisse Listesi Çekiliyor..."):
        try:
            raw_tickers = get_all_tickers()
            bist_tickers = [f"{ticker}.IS" for ticker in raw_tickers if not ticker.endswith(('F', 'BY', 'E'))]
            st.success(f"Toplam {len(bist_tickers)} aktif hisse senedi listelendi. Tarama başlıyor...")
        except Exception as e:
            st.error(f"Hisse listesi alınamadı: {e}")
            bist_tickers = ["THYAO.IS", "EUREN.IS", "ADEL.IS"]

    found_stocks = []
    
    # İlerleme Çubuğu (Progress Bar)
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_tickers = len(bist_tickers)

    for index, ticker in enumerate(bist_tickers, 1):
        # Arayüzü güncelleme
        percent_complete = int((index / total_tickers) * 100)
        progress_bar.progress(percent_complete)
        status_text.text(f"Kontrol ediliyor ({index}/{total_tickers}): {ticker.replace('.IS', '')}")
        
        try:
            df = yf.download(ticker, period="6mo", progress=False)
            if df.empty or len(df) < 100:
                continue
                
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)

            close = df['Close']
            volume = df['Volume']
            high = df['High']
            low = df['Low']
            
            # İndikatörler
            ema20 = ta.ema(close, length=20)
            sma100 = ta.sma(close, length=100)
            rsi14 = ta.rsi(close, length=14)
            adx14 = ta.adx(high, low, close, length=14)['ADX_14']
            
            macd = ta.macd(close, fast=12, slow=26, signal=9)
            macd_line = macd['MACD_12_26_9']
            signal_line = macd['MACDs_12_26_9']
            
            vol_sma10 = ta.sma(volume, length=10)
            vol_sma30 = ta.sma(volume, length=30)
            
            # Koşullar
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
            
            if all([cond1, cond2, cond3, cond4, cond5, cond6, cond7, cond8, cond9, cond10]):
                clean_name = ticker.replace('.IS', '')
                found_stocks.append(clean_name)
                # Ekrana anlık düşen hisseyi bas
                st.toast(f"✨ Sinyal Yakalandı: {clean_name}", icon="🔥")
                
        except Exception:
            pass

    # Tarama Bitince Sonuçları Göster
    status_text.text("Tarama tamamlandı!")
    st.divider()
    
    st.subheader("🎯 Tarama Sonuçları")
    if found_stocks:
        st.success(f"Bugün şartları sağlayan {len(found_stocks)} hisse bulundu:")
        
        # Sonuçları güzel bir tablo/kart mimarisiyle gösterelim
        cols = st.columns(4)
        for i, stock in enumerate(found_stocks):
            with cols[i % 4]:
                st.info(f"📈 **{stock}**")
    else:
        st.warning("Bugün 10/10 şartı sağlayan herhangi bir BIST hissesi bulunamadı.")
