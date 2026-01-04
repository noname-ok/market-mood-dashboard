import streamlit as st
import yfinance as yf
from textblob import TextBlob
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Market Mood Dashboard", layout="wide")

# --- HEADER & INTRODUCTION ---
st.title("📈 Market Mood: AI-Powered Financial Dashboard")
st.markdown("""
**The Problem:** Stock charts tell you *what* happened. They don't tell you *how* people feel.
**The Solution:** This tool combines **Real-time Market Data** with **NLP Sentiment Analysis** to gauge investor confidence.
""")

# --- SIDEBAR (User Input) ---
st.sidebar.header("Configuration")
ticker_symbol = st.sidebar.text_input("Enter Stock Ticker (e.g., AAPL, TSLA, GOOG)", "TSLA")
time_period = st.sidebar.selectbox("Select Time Period", ["1mo", "3mo", "6mo", "1y"])

# --- CORE FUNCTIONS ---

def get_stock_data(symbol, period):
    """Fetches historical stock data using yfinance."""
    stock = yf.Ticker(symbol)
    data = stock.history(period=period)
    return data, stock.news

def analyze_sentiment(news_list):
    """
    Analyzes news headlines using TextBlob (NLP).
    Returns: Average polarity (-1 to 1) and a dataframe of news with scores.
    """
    if not news_list:
        return 0, pd.DataFrame()

    sentiments = []
    news_data = []

    for item in news_list:
        title = item.get('title', '')
        link = item.get('link', '')
        
        # --- THE AI PART ---
        # TextBlob calculates polarity: -1 (Negative) to +1 (Positive)
        blob = TextBlob(title)
        polarity = blob.sentiment.polarity
        
        sentiments.append(polarity)
        news_data.append({'Title': title, 'Sentiment Score': polarity, 'Link': link})

    avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
    return avg_sentiment, pd.DataFrame(news_data)

# --- MAIN EXECUTION ---

if ticker_symbol:
    try:
        # 1. Fetch Data
        with st.spinner('Fetching market data and analyzing news...'):
            stock_df, stock_news = get_stock_data(ticker_symbol, time_period)
            avg_score, news_df = analyze_sentiment(stock_news)

        # 2. Display Key Metrics
        col1, col2, col3 = st.columns(3)
        
        # Metric: Current Price
        current_price = stock_df['Close'].iloc[-1]
        col1.metric("Current Price", f"${current_price:.2f}")
        
        # Metric: Sentiment Score
        # Logic: > 0 is Positive, < 0 is Negative
        if avg_score > 0.1:
            sentiment_label = "Positive 🟢"
        elif avg_score < -0.1:
            sentiment_label = "Negative 🔴"
        else:
            sentiment_label = "Neutral ⚪"
            
        col2.metric("Market Sentiment (AI Analysis)", sentiment_label, f"{avg_score:.2f}")

        # 3. Visualize Price (Interactive Chart)
        st.subheader(f"Price Trend: {ticker_symbol.upper()}")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=stock_df.index, y=stock_df['Close'], mode='lines', name='Close Price'))
        st.plotly_chart(fig, use_container_width=True)

        # 4. Visualize Sentiment (The "Why")
        st.subheader("📰 Recent News & Sentiment Analysis")
        st.write("The AI analyzed the following headlines to calculate the score:")
        
        # Color code the dataframe for visual impact
        def color_sentiment(val):
            color = 'green' if val > 0 else 'red' if val < 0 else 'grey'
            return f'color: {color}'

        st.dataframe(
            news_df[['Title', 'Sentiment Score']].style.map(color_sentiment, subset=['Sentiment Score']),
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Error: Could not find data for {ticker_symbol}. Please check the ticker symbol.")