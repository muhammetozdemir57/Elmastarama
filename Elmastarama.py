import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
import warnings

warnings.filterwarnings('ignore')

# --- BIST Hisselerini İş Yatırım API'sinden Çeken Fonksiyon ---
def get_bist_tickers():
    url = "https://www.isyatirim.com.tr/_layouts/15/IsYatirim.Website/Common/Data.aspx/HisseOku"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    response = requests.get(url, headers=headers, timeout=10)
    data = response.json()
    
    # Sadece 4 veya 5 harfli standart hisse kodlarını al (Varant ve Fonları filtreler)
    tickers = [item['hisseCodu'] for item in data['value'] if len(item['hisseCodu']) <= 5]
    
    # Yahoo Finance formatına (.IS) çevir
    return [f"{t}.IS" for t in tickers]

# --- Sayfa Yapılandırması ---
st.set_page_config(page_title="BIST Dip Elmas Tarayıcı", page_icon="💎", layout="wide")

st.title("💎 BIST - Dip Elmas Oluşumu Tarayıcısı")
st.write("Bu sistem, Borsa İstanbul'daki güncel hisseleri 10 farklı teknik analiz kriterine göre canlı olarak tarar.")

# --- Tarama Butonu ---
if st.button("Taramayı Başlat (Canlı Veri)", type="primary"):
    
    with st.spinner("Güncel BIST Hisse Listesi Çekiliyor..."):
        try:
            bist_tickers = get_bist_tickers()
            st.success(f"Toplam {len(bist_tickers)} aktif hisse senedi listelendi. Tarama başlıyor...")
        except Exception as e:
            st.error(f"Hisse listesi alınamadı: {e}")
            bist_tickers = ["THYAO.IS", "EUREN.IS", "ADEL.IS", "KOCMT.IS", "KOPOL.IS"] # Hata anında yedek liste

    found_stocks = []
    
    # İlerleme Çubuğu
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
            
            # 10 Maddelik Koşullar
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
            
            # Tüm şartlar sağlanıyorsa listeye ekle
            if all([cond1, cond2, cond3, cond4, cond5, cond6, cond7, cond8, cond9, cond10]):
                clean_name = ticker.replace('.IS', '')
                found_stocks.append(clean_name)
                st.toast(f"✨ Sinyal Yakalandı: {clean_name}", icon="🔥")
                
        except Exception:
            pass

    # Tarama Bitince Sonuçları Göster
    status_text.text("Tarama tamamlandı!")
    st.divider()
    
    st.subheader("🎯 Tarama Sonuçları")
    if found_stocks:
        st.success(f"Bugün şartları sağlayan {len(found_stocks)} hisse bulundu:")
        
        cols = st.columns(4)
        for i, stock in enumerate(found_stocks):
            with cols[i % 4]:
                st.info(f"📈 **{stock}**")
    else:
        st.warning("Bugün 10/10 şartı sağlayan herhangi bir BIST hissesi bulunamadı.")
