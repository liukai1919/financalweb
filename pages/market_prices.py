import os
from langchain_openai import ChatOpenAI
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import yfinance as yf
import dotenv
import plotly.graph_objects as go
from datetime import datetime, timedelta
from components.sidebar import show_sidebar, get_language
from utils.config import load_config
import urllib.parse
import feedparser

dotenv.load_dotenv()

# 加载配置
if 'config_loaded' not in st.session_state:
    config = load_config()
    st.session_state.language = config['language']
    st.session_state.ai_model = config['ai_model']
    st.session_state.config_loaded = True

# 设置页面配置
st.set_page_config(
    page_title="市场价格" if get_language() == "zh" else "Market Prices",
    page_icon="💱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 显示侧边栏
show_sidebar()

# 初始化 ChatOpenAI
llm = ChatOpenAI(
    model="o1-mini"
)

# 函数定义
def get_forex_rate(from_currency, to_currency):
    url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
    try:
        response = requests.get(url)
        data = response.json()
        return data['rates'][to_currency]
    except Exception as e:
        return f"Error: {str(e)}"

def get_crypto_price(symbol):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    try:
        response = requests.get(url)
        data = response.json()
        return float(data['price'])
    except Exception as e:
        return f"Error: {str(e)}"

def get_gold_price():
    api_key = os.getenv("GOLD_API_KEY")
    if api_key is None:
        raise ValueError("GOLD_API_KEY not found in environment variables")
    symbol = "XAU"
    curr = "USD"
    date = ""

    url = f"https://www.goldapi.io/api/{symbol}/{curr}{date}"
    
    headers = {
        "x-access-token": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        result = response.json()
        return result['ask']
    except requests.exceptions.RequestException as e:
        print("Error:", str(e))

# 获取历史数据的函数
def get_historical_data(symbol, period="1mo"):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        return hist
    except Exception as e:
        print(f"获取历史数据时出错: {str(e)}")
        return None

def analyze_trend(data, asset_name, period):
    """使用 LLM 分析价格趋势"""
    try:
        cache_key = f'trend_analysis_{asset_name}_{period}_{get_language()}'
        if cache_key in st.session_state:
            return st.session_state[cache_key]
            
        # 检查是否设置了 API Key
        api_key = st.session_state.get('openai_api_key')
        if not api_key:
            return ("请在设置页面配置 OpenAI API Key" if get_language() == "zh" 
                   else "Please configure OpenAI API Key in settings")
        
        # 使用配置的 API Key
        os.environ["OPENAI_API_KEY"] = api_key
        
        # 使用配置的模型
        model = st.session_state.get('ai_model', 'gpt-3.5-turbo')
        llm = ChatOpenAI(model=model)
        
        with st.spinner('正在分析市场趋势...' if get_language() == "zh" else 'Analyzing market trends...'):
            current_price = data['Close'].iloc[-1]
            start_price = data['Close'].iloc[0]
            price_change = ((current_price - start_price) / start_price) * 100
            
            if get_language() == "zh":
                prompt = f"""
                请分析{asset_name}的市场趋势：

                当前价格：{current_price:.2f}
                价格变动：{price_change:.2f}%
                时间周期：{period}

                请提供以下分析：
                1. 价格趋势
                2. 波动特征
                3. 影响因素
                4. 市场展望

                请用中文回答，并使用markdown格式。
                """
            else:
                prompt = f"""
                Please analyze the market trend for {asset_name}:

                Current Price: {current_price:.2f}
                Price Change: {price_change:.2f}%
                Time Period: {period}

                Please provide analysis on:
                1. Price Trend
                2. Volatility Characteristics
                3. Influencing Factors
                4. Market Outlook

                Please respond in English using markdown format.
                """
            
            analysis = llm.invoke(prompt)
            result = analysis.content if hasattr(analysis, 'content') else str(analysis)
            st.session_state[cache_key] = result
            return result
            
    except Exception as e:
        return f"{'分析过程出现错误' if get_language() == 'zh' else 'Analysis error'}: {str(e)}"

def get_financial_news(topic, num_news=8):
    """获取最近一周的金融新闻"""
    try:
        # URL编码搜索词
        encoded_topic = urllib.parse.quote(topic)
        
        # 根据语言设置选择不同的 Google News 参数
        lang = get_language()
        hl = "zh-CN" if lang == "zh" else "en"
        gl = "CN" if lang == "zh" else "US"
        
        # 构建 Google News RSS URL，添加时间参数以获取最近一周的新闻
        rss_url = f"https://news.google.com/rss/search?q={encoded_topic}&hl={hl}&gl={gl}&ceid={gl}:{hl}&tbs=qdr:w"
        
        # 解析 RSS feed
        feed = feedparser.parse(rss_url)
        
        # 检查是否成功获取新闻
        if not feed.entries:
            return []
        
        # 获取当前时间和一周前的时间
        one_week_ago = datetime.now() - timedelta(days=7)
        
        # 提取新闻
        news_list = []
        for entry in feed.entries:
            try:
                # 解析发布时间
                published_time = datetime(*entry.published_parsed[:6])
                
                # 只保留最近一周的新闻
                if published_time >= one_week_ago:
                    news_list.append({
                        'title': entry.title,
                        'link': entry.link,
                        'published': entry.published,
                        'source': entry.source.title if hasattr(entry, 'source') else "未知来源"
                    })
                if len(news_list) >= num_news:
                    break
            except AttributeError:
                continue
        
        return news_list
    except Exception as e:
        st.error(f"获取新闻时出错: {str(e)}")
        return []

def generate_market_analysis(topic, historical_data):
    """生成市场分析"""
    try:
        cache_key = f'market_analysis_{datetime.now().strftime("%Y-%m-%d")}_{get_language()}'
        if cache_key in st.session_state:
            return st.session_state[cache_key]
            
        # 检查是否设置了 API Key
        api_key = st.session_state.get('openai_api_key')
        if not api_key:
            return ("请在设置页面配置 OpenAI API Key" if get_language() == "zh" 
                   else "Please configure OpenAI API Key in settings")
        
        # 使用配置的 API Key
        os.environ["OPENAI_API_KEY"] = api_key
        
        # 使用配置的模型
        model = st.session_state.get('ai_model', 'gpt-3.5-turbo')
        llm = ChatOpenAI(model=model)
        
        # 获取最近一周的新闻
        news = get_financial_news(topic)  # 使用传入的主题搜索相关的新闻
        news_content = "\n".join([f"- {item['title']} (来源: {item['source']})" for item in news]) if news else "没有找到相关新闻。"

        # 生成最近走势数据的描述
        historical_data_description = historical_data.tail(5).to_string()  # 获取最近5天的走势数据

        # 根据当前语言选择提示词
        if get_language() == "zh":
            prompt = f"""
            请分析以下市场数据并生成详细报告：

            主题: {topic}

            最近走势数据：
            {historical_data_description}

            相关新闻：
            {news_content}

            请提供分析。
            """
        else:
            prompt = f"""
            Please analyze the following market data and generate a detailed report:

            Topic: {topic}

            Recent Trend Data:
            {historical_data_description}

            Related News:
            {news_content}

            Please provide the analysis.
            """
        
        with st.spinner('正在生成分析报告...' if get_language() == "zh" else 'Generating analysis...'):
            analysis = llm.invoke(prompt)
            return analysis.content if hasattr(analysis, 'content') else str(analysis)
            
    except Exception as e:
        return (f"生成分析报告时出错: {str(e)}" if get_language() == "zh" 
                else f"Error generating analysis: {str(e)}")

# 页面布局
st.title("💱 " + ("市场价格" if get_language() == "zh" else "Market Prices"))

# 添加返回主页按钮
if st.sidebar.button("🏠 返回主页"):
    st.switch_page("app.py")

# 选择时间范围
period = st.selectbox(
    "选择时间范围" if get_language() == "zh" else "Select Time Range",
    ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"],
    index=2
)

# 创建标签页
tabs = st.tabs([
    "外汇" if get_language() == "zh" else "Forex",
    "黄金" if get_language() == "zh" else "Gold",
    "加密货币" if get_language() == "zh" else "Crypto"
])

with tabs[0]:  # 外汇标签页
    st.subheader("USD/CNY " + ("汇率走势" if get_language() == "zh" else "Exchange Rate"))
    # 美元/人民币走势
    forex_hist_usd = get_historical_data("CNY=X", period=period)
    usd_cny_rate = forex_hist_usd['Close'].iloc[-1] if forex_hist_usd is not None else None  # 获取最新汇率
    # 加元/人民币走势
    forex_hist_cad = get_historical_data("CADCNY=X", period=period)
    cad_cny_rate = forex_hist_cad['Close'].iloc[-1] if forex_hist_cad is not None else None  # 获取最新汇率
    if forex_hist_usd is not None:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=forex_hist_usd.index, y=forex_hist_usd['Close'], name='USD/CNY'))
        fig.update_layout(
            title='USD/CNY ' + ("汇率走势" if get_language() == "zh" else "Exchange Rate"),
            yaxis_title=("汇率" if get_language() == "zh" else "Rate"),
            template='plotly_dark'
        )
        st.plotly_chart(fig)
    with st.expander("💡 " + ("AI 分析" if get_language() == "zh" else "AI Analysis")):
        if st.button("生成分析", key="usd_cny_analysis"):
            currency_topic = "USD/CNY 汇率"  # 设置主题为外汇
            historical_data_usd = get_historical_data("CNY=X", period=period)  # 获取美元/人民币的历史数据
            analysis = generate_market_analysis(currency_topic, historical_data_usd)
            st.write(analysis)
            st.toast("分析结果已生成！" if get_language() == "zh" else "Analysis generated!")

    # 加元/人民币走势
    forex_hist_cad = get_historical_data("CADCNY=X", period=period)
    if forex_hist_cad is not None:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=forex_hist_cad.index, y=forex_hist_cad['Close'], name='CAD/CNY'))
        fig.update_layout(
            title='加元/人民币汇率走势',
            yaxis_title='汇率',
            template='plotly_dark'
        )
        st.plotly_chart(fig)
    

    with st.expander("💡 " + ("AI 分析" if get_language() == "zh" else "AI Analysis")):
        if st.button("生成分析", key="cad_cny_analysis"):   
            currency_topic = "CAD/CNY 汇率"  # 设置主题为外汇
            historical_data_cad = get_historical_data("CADCNY=X", period=period)  # 获取美元/人民币的历史数据
            analysis = generate_market_analysis(currency_topic, historical_data_cad)
            st.write(analysis)
            st.toast("分析结果已生成！" if get_language() == "zh" else "Analysis generated!")

with tabs[1]:  # 黄金标签页
    st.subheader("黄金价格" if get_language() == "zh" else "Gold Price")
    gold_price = get_gold_price()
    currency_topic = "黄金价格"  # 设置主题为黄金
    if isinstance(gold_price, (int, float)):
        st.write(f"$ {gold_price:.2f}/{'盎司' if get_language() == 'zh' else 'oz'}")
    else:
        st.write("获取黄金价格失败")  # 提示获取失败

    # 黄金走势
    gold_hist = get_historical_data("GC=F", period=period)
    if gold_hist is not None:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=gold_hist.index, y=gold_hist['Close'], name='Gold'))
        fig.update_layout(
            title='黄金价格走势',
            yaxis_title='美元/盎司',
            template='plotly_dark'
        )
        st.plotly_chart(fig)

    with st.expander("💡 " + ("AI 分析" if get_language() == "zh" else "AI Analysis")):
        if st.button("生成分析", key="gold_analysis"):
            currency_topic = "黄金价格"  # 设置主题为黄金
            historical_data_gold = get_historical_data("GC=F", period=period)  # 获取黄金的历史数据
            analysis = generate_market_analysis(currency_topic, historical_data_gold)
            st.write(analysis)
            st.toast("分析结果已生成！" if get_language() == "zh" else "Analysis generated!")

with tabs[2]:  # 加密货币标签页
    st.subheader("加密货币" if get_language() == "zh" else "Crypto")
    currency_topic = "比特币 加密货币"  # 设置主题为加密货币
    # 获取比特币和以太坊的价格
    btc_hist = get_historical_data("BTC-USD", period=period)
    eth_hist = get_historical_data("ETH-USD", period=period)
    if btc_hist is not None:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=btc_hist.index, y=btc_hist['Close'], name='BTC'))
        fig.update_layout(
            title='比特币价格走势',
            yaxis_title='美元',
            template='plotly_dark'
        )
        st.plotly_chart(fig)

    with st.expander("💡 " + ("AI 分析" if get_language() == "zh" else "AI Analysis")):
        if st.button("生成分析", key="btc_analysis"):
            currency_topic = "比特币 加密货币"  # 设置主题为加密货币
            historical_data_btc = get_historical_data("BTC-USD", period=period)  # 获取比特币的历史数据
            analysis = generate_market_analysis(currency_topic, historical_data_btc)
            st.write(analysis)
            st.toast("分析结果已生成！" if get_language() == "zh" else "Analysis generated!")
    
    # 以太坊走势
    eth_hist = get_historical_data("ETH-USD", period=period)
    if eth_hist is not None:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=eth_hist.index, y=eth_hist['Close'], name='ETH'))
        fig.update_layout(
            title='以太坊价格走势',
            yaxis_title='美元',
            template='plotly_dark'
        )
        st.plotly_chart(fig)
        
    with st.expander("💡 " + ("AI 分析" if get_language() == "zh" else "AI Analysis")):
        if st.button("生成分析", key="eth_analysis"):
            currency_topic = "以太坊 加密货币"  # 设置主题为加密货币
            historical_data_eth = get_historical_data("ETH-USD", period=period)  # 获取以太坊的历史数据
            analysis = generate_market_analysis(currency_topic, historical_data_eth)
            st.write(analysis)
            st.toast("分析结果已生成！" if get_language() == "zh" else "Analysis generated!")
        
    # Solana走势
    sol_hist = get_historical_data("SOL-USD", period=period)
    if sol_hist is not None:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=sol_hist.index, y=sol_hist['Close'], name='SOL'))
        fig.update_layout(
            title='Solana价格走势',
            yaxis_title='美元',
            template='plotly_dark'
        )
        st.plotly_chart(fig)

    with st.expander("💡 " + ("AI 分析" if get_language() == "zh" else "AI Analysis")):
        if st.button("生成分析", key="sol_analysis"):
            currency_topic = "Solana 加密货币"  # 设置主题为加密货币
            historical_data_sol = get_historical_data("SOL-USD", period=period)  # 获取Solana的历史数据
            analysis = generate_market_analysis(currency_topic, historical_data_sol)
            st.write(analysis)
            st.toast("分析结果已生成！" if get_language() == "zh" else "Analysis generated!")

# 添加刷新按钮
if st.button('🔄 ' + ("刷新数据" if get_language() == "zh" else "Refresh Data")):
    st.rerun()

# 显示最后更新时间
st.text(("最后更新时间: " if get_language() == "zh" else "Last Updated: ") + 
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')) 

# 更新图表标题和标签
def create_exchange_rate_chart(data, title):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['Close'],
        mode='lines',
        name=("汇率" if get_language() == "zh" else "Exchange Rate")
    ))
    
    fig.update_layout(
        title=title,
        yaxis_title=("汇率" if get_language() == "zh" else "Exchange Rate"),
        xaxis_title=("日期" if get_language() == "zh" else "Date"),
        template='plotly_dark'
    )
    return fig

def create_gold_chart(data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['Close'],
        mode='lines',
        name=("黄金价格" if get_language() == "zh" else "Gold Price")
    ))
    
    fig.update_layout(
        title=("黄金价格走势" if get_language() == "zh" else "Gold Price Trend"),
        yaxis_title=("价格 (USD/盎司)" if get_language() == "zh" else "Price (USD/oz)"),
        xaxis_title=("日期" if get_language() == "zh" else "Date"),
        template='plotly_dark'
    )
    return fig 