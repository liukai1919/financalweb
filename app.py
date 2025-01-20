import streamlit as st
from components.sidebar import show_sidebar, get_language
import yfinance as yf
import pandas as pd
from datetime import datetime
import requests
from utils.config import load_config


# 加载配置
if 'config_loaded' not in st.session_state:
    config = load_config()
    st.session_state.language = config['language']
    st.session_state.ai_model = config['ai_model']
    st.session_state.config_loaded = True
    st.session_state.theme = config['theme']
    st.session_state.openai_api_key = config['openai_api_key']

# 设置页面配置
st.set_page_config(
    page_title="金融数据分析平台" if get_language() == "zh" else "Financial Analysis Platform",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 设置主题
if 'theme' in st.session_state:
    with open('.streamlit/config.toml', 'r') as f:
        config_content = f.read()
    
    # 替换主题设置
    config_content = config_content.replace('${theme}', st.session_state.theme)
    
    with open('.streamlit/config.toml', 'w') as f:
        f.write(config_content)

# 显示侧边栏
show_sidebar()

# 页面标题
st.title("🏦 " + ("金融数据分析平台" if get_language() == "zh" else "Financial Analysis Platform"))

# 欢迎信息
st.markdown(
    "👋 " + 
    ("欢迎使用金融数据分析平台！" if get_language() == "zh" else "Welcome to the Financial Analysis Platform!")
)

# 功能介绍
st.subheader("🎯 " + ("主要功能" if get_language() == "zh" else "Main Features"))

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 📈 " + ("股票分析" if get_language() == "zh" else "Stock Analysis"))
    st.write(
        "实时股票数据分析和预测" if get_language() == "zh" else 
        "Real-time stock data analysis and prediction"
    )

with col2:
    st.markdown("### 💱 " + ("市场价格" if get_language() == "zh" else "Market Prices"))
    st.write(
        "全球市场价格监控与分析" if get_language() == "zh" else 
        "Global market price monitoring and analysis"
    )

with col3:
    st.markdown("### 📰 " + ("金融新闻" if get_language() == "zh" else "Financial News"))
    st.write(
        "实时金融新闻与AI分析" if get_language() == "zh" else 
        "Real-time financial news with AI analysis"
    )

# 使用说明
st.subheader("📖 " + ("使用说明" if get_language() == "zh" else "Instructions"))
st.write(
    """
    1. """ + (
    "使用左侧菜单导航不同功能模块" if get_language() == "zh" else 
    "Use the left menu to navigate different modules"
) + """
    2. """ + (
    "在每个模块中可以查看详细的数据分析" if get_language() == "zh" else 
    "View detailed data analysis in each module"
) + """
    3. """ + (
    "支持实时数据更新和AI分析" if get_language() == "zh" else 
    "Support real-time data updates and AI analysis"
) + """
    """
)

# 版本信息
st.sidebar.markdown("---")
st.sidebar.caption(
    "版本 1.0.0" if get_language() == "zh" else "Version 1.0.0"
)

def get_stock_price(symbol):
    """获取股票/指数最新价格"""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period='1d')
        if not data.empty:
            current_price = data['Close'].iloc[-1]
            price_change = ((current_price - data['Open'].iloc[0]) / data['Open'].iloc[0]) * 100
            return current_price, price_change
        return None, None
    except Exception as e:
        return None, None

def get_crypto_price(symbol):
    """获取加密货币价格"""
    try:
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
        response = requests.get(url)
        data = response.json()
        return float(data['lastPrice']), float(data['priceChangePercent'])
    except Exception as e:
        return None, None

# 显示市场概览
st.subheader("📊 " + ("市场概览" if get_language() == "zh" else "Market Overview"))

# 创建三列布局
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🌎 " + ("主要指数" if get_language() == "zh" else "Major Indices"))
    
    # 美股三大指数
    indices = {
        '^GSPC': 'S&P 500',
        '^DJI': 'Dow Jones',
        '^IXIC': 'NASDAQ',
        # A股指数
        '000001.SS': '上证指数' if get_language() == "zh" else 'SSE Composite',
        '399001.SZ': '深证成指' if get_language() == "zh" else 'SZSE Component'
    }
    
    for symbol, name in indices.items():
        price, change = get_stock_price(symbol)
        if price and change:
            color = "green" if change >= 0 else "red"
            st.markdown(
                f"{name}: {price:.2f} "
                f"<span style='color:{color}'>({change:+.2f}%)</span>",
                unsafe_allow_html=True
            )

with col2:
    st.markdown("### 💱 " + ("汇率" if get_language() == "zh" else "Exchange Rates"))
    
    # 美元和加元兑人民币
    currencies = {
        'CNY=X': 'USD/CNY',
        'CADCNY=X': 'CAD/CNY'
    }
    
    for symbol, name in currencies.items():
        price, change = get_stock_price(symbol)
        if price and change:
            color = "green" if change >= 0 else "red"
            st.markdown(
                f"{name}: {price:.4f} "
                f"<span style='color:{color}'>({change:+.2f}%)</span>",
                unsafe_allow_html=True
            )
    
    # 黄金价格
    gold_price, gold_change = get_stock_price('GC=F')
    if gold_price and gold_change:
        color = "green" if gold_change >= 0 else "red"
        st.markdown(
            f"{'黄金' if get_language() == 'zh' else 'Gold'}: {gold_price:.2f} "
            f"<span style='color:{color}'>({gold_change:+.2f}%)</span>",
            unsafe_allow_html=True
        )

with col3:
    st.markdown("### 🪙 " + ("加密货币" if get_language() == "zh" else "Cryptocurrencies"))
    
    # 主要加密货币
    cryptos = {
        'BTCUSDT': 'Bitcoin',
        'ETHUSDT': 'Ethereum',
        'SOLUSDT': 'Solana'
    }
    
    for symbol, name in cryptos.items():
        price, change = get_crypto_price(symbol)
        if price and change:
            color = "green" if change >= 0 else "red"
            st.markdown(
                f"{name}: ${price:,.2f} "
                f"<span style='color:{color}'>({change:+.2f}%)</span>",
                unsafe_allow_html=True
            )

# 添加自动刷新按钮
if st.button('🔄 ' + ("刷新数据" if get_language() == "zh" else "Refresh Data")):
    st.rerun()

# 显示最后更新时间
st.caption(("最后更新时间: " if get_language() == "zh" else "Last Updated: ") + 
           datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


