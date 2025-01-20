import streamlit as st

# 必须是第一个 Streamlit 命令
st.set_page_config(
    page_title="Cryptocurrency Analysis",
    page_icon="🪙",
    layout="wide"
)

import os
from langchain_openai import ChatOpenAI
from datetime import datetime, timedelta
import urllib.parse
import feedparser
import requests
import pandas as pd

from components.sidebar import show_sidebar
from utils.language import get_language

# 读取 coins.csv 文件并创建加密货币名称与 CoinGecko ID 的映射
def load_crypto_data():
    try:
        df = pd.read_csv('coins.csv')  # 读取 CSV 文件
        return {row['name']: row['id'] for index, row in df.iterrows()}  # 创建字典映射
    except Exception as e:
        st.error(f"加载加密货币数据时出错: {str(e)}")
        return {}

# 加密货币 ID 映射
crypto_id_map = load_crypto_data()

def load_api_key():
    """加载 OpenAI API Key"""
    if 'openai_api_key' not in st.session_state:
        st.session_state['openai_api_key'] = os.getenv("OPENAI_API_KEY", "")
    
    if not st.session_state['openai_api_key']:
        st.session_state['openai_api_key'] = st.text_input("请输入 OpenAI API Key", type="password")

show_sidebar()

def get_crypto_news(crypto_name, num_news=5):
    """根据加密货币名称获取最近一周的新闻"""
    try:
        # URL编码加密货币名称
        encoded_crypto_name = urllib.parse.quote(crypto_name)
        
        # 正确的 Google News RSS URL
        language = "zh-CN" if get_language() == "zh" else "en-US"
        rss_url = f"https://news.google.com/rss/search?q={encoded_crypto_name}+when:7d&hl={language}&gl=CN&ceid=CN:zh-CN"
        
        # 解析 RSS feed
        feed = feedparser.parse(rss_url)
        
        # 检查是否成功获取新闻
        if not feed.entries:
            return []
        
        # 提取新闻
        news_list = []
        for entry in feed.entries[:num_news]:  # 限制新闻数量
            try:
                news_item = {
                    'title': entry.title,
                    'link': entry.link,
                    'published': entry.published,
                    'source': getattr(entry, 'source', {'title': "未知来源"}).get('title', "未知来源")
                }
                news_list.append(news_item)
            except (AttributeError, TypeError) as e:
                st.warning(f"处理新闻条目时出错: {str(e)}")
                continue
                
        return news_list
    except Exception as e:
        st.error(f"获取新闻时出错: {str(e)}")
        return []

def get_crypto_price(crypto_name):
    """根据加密货币名称获取当前价格"""
    crypto_id = crypto_id_map.get(crypto_name)
    
    if not crypto_id:
        st.error("未找到该加密货币，请检查名称。" if get_language() == "zh" else "Cryptocurrency not found, please check the name.")
        return None
    
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_id}&vs_currencies=usd"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        return data[crypto_id]['usd']  # 返回加密货币的美元价格
    else:
        error_msg = f"获取价格时出错: {response.status_code}" if get_language() == "zh" else f"Error fetching price: {response.status_code}"
        st.error(error_msg)
        return None

def analyze_trend(crypto_data, crypto_name, period, news_content):
    """使用LangChain和OpenAI分析加密货币趋势"""
    try:
        cache_key = f'crypto_analysis_{crypto_name}_{period}_{get_language()}'
        if cache_key in st.session_state:
            return st.session_state[cache_key]
        
        api_key = st.session_state.get('openai_api_key')
        if not api_key:
            return ("请在设置页面配置 OpenAI API Key" if get_language() == "zh" 
                   else "Please configure OpenAI API Key in settings")
        
        os.environ["OPENAI_API_KEY"] = api_key
        
        model = st.session_state.get('ai_model', 'gpt-3.5-turbo')
        llm = ChatOpenAI(model=model)
        
        with st.spinner('正在生成分析报告...' if get_language() == "zh" else 'Generating analysis...'):
            latest_price = crypto_data['Close'].iloc[-1]
            price_change = (latest_price - crypto_data['Close'].iloc[0]) / crypto_data['Close'].iloc[0] * 100
            avg_volume = crypto_data['Volume'].mean()
            
            if get_language() == "zh":
                prompt = f"""
                请分析以下加密货币数据并生成详细报告：

                加密货币：{crypto_name}
                当前价格：${latest_price:.2f}
                期间涨跌幅：{price_change:.2f}%
                平均成交量：{avg_volume:,.0f}

                相关新闻：
                {news_content}

                请提供以下方面的分析：
                1. 价格趋势分析
                2. 成交量分析
                3. 投资建议
                4. 风险评估
                5. 未来展望
                6. 新闻影响
                请用中文回答，并使用markdown格式。
                """
            else:
                prompt = f"""
                Please analyze the following cryptocurrency data and generate a detailed report:

                Cryptocurrency: {crypto_name}
                Current Price: ${latest_price:.2f}
                Period Change: {price_change:.2f}%
                Average Volume: {avg_volume:,.0f}

                Related News:
                {news_content}

                Please provide analysis on:
                1. Price Trend Analysis
                2. Volume Analysis
                3. Investment Recommendations
                4. Risk Assessment
                5. Future Outlook
                6. News Impact
                Please respond in English using markdown format.
                """
            
            analysis = llm.invoke(prompt)
            analysis_content = analysis.content if hasattr(analysis, 'content') else str(analysis)
            st.session_state[cache_key] = analysis_content
            return analysis_content
            
    except Exception as e:
        return (f"生成分析报告时出错: {str(e)}" if get_language() == "zh" 
                else f"Error generating analysis: {str(e)}")

def get_historical_data(crypto_name, period):
    """获取加密货币的历史数据"""
    days_mapping = {
        "1天": 1,
        "1周": 7,
        "1个月": 30,
        "3个月": 90  # 添加更多时间选项
    }
    
    try:
        crypto_id = crypto_id_map.get(crypto_name)
        if not crypto_id:
            st.error("未找到该加密货币，请检查名称。")
            return pd.DataFrame()
            
        url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}/market_chart"
        days = days_mapping.get(period, 7)
        
        params = {
            'vs_currency': 'usd',
            'days': days,
            'interval': 'daily'
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()  # 添加错误检查
        
        data = response.json()
        
        # 使用列表推导式优化数据处理
        df = pd.DataFrame({
            'timestamp': [pd.to_datetime(price[0], unit='ms') for price in data['prices']],
            'Close': [price[1] for price in data['prices']],
            'Volume': [volume[1] for volume in data['total_volumes']]
        })
        
        return df
        
    except requests.exceptions.RequestException as e:
        st.error(f"API请求失败: {str(e)}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"处理数据时出错: {str(e)}")
        return pd.DataFrame()

def main():
    st.title("加密货币分析" if get_language() == "zh" else "Cryptocurrency Analysis")
    load_api_key()

    # 添加缓存装饰器
    @st.cache_data(ttl=3600)  # 缓存1小时
    def load_cached_crypto_data():
        return load_crypto_data()
    
    crypto_id_map = load_cached_crypto_data()
    
    # 使用容器来控制内容宽度
    with st.container():
        crypto_id_map = load_cached_crypto_data()
        
        # 将选择器放在同一行
        col1, col2 = st.columns([2, 1])
        with col1:
            crypto_name = st.selectbox(
                "选择加密货币" if get_language() == "zh" else "Select Cryptocurrency",
                options=list(crypto_id_map.keys()),
                index=None,
                placeholder="请选择加密货币..." if get_language() == "zh" else "Select a cryptocurrency..."
            )
        with col2:
            period_options = {
                "zh": ["1天", "1周", "1个月", "3个月"],
                "en": ["1 Day", "1 Week", "1 Month", "3 Months"]
            }
            period = st.selectbox(
                "选择分析周期" if get_language() == "zh" else "Select Period",
                period_options["zh" if get_language() == "zh" else "en"],
                index=1
            )

        if st.button(
            "获取数据" if get_language() == "zh" else "Get Data", 
            type="primary", 
            use_container_width=True
        ):
            if not crypto_name:
                st.error("请选择加密货币" if get_language() == "zh" else "Please select a cryptocurrency")
                st.stop()
                
            with st.spinner("正在获取数据..." if get_language() == "zh" else "Fetching data..."):
                current_price = get_crypto_price(crypto_name)
                if current_price:
                    st.metric(
                        label=f"{crypto_name}" + ("当前价格" if get_language() == "zh" else " Current Price"),
                        value=f"${current_price:,.2f}"
                    )
                    
                crypto_data = get_historical_data(crypto_name, period)
                
                if not crypto_data.empty:
                    # 创建三个标签页：图表、AI分析、新闻
                    tab_labels = {
                        "zh": ["📈 价格走势", "🤖 AI分析", "📰 相关新闻"],
                        "en": ["📈 Price Trend", "🤖 AI Analysis", "📰 Related News"]
                    }
                    current_labels = tab_labels["zh" if get_language() == "zh" else "en"]
                    tab1, tab2, tab3 = st.tabs(current_labels)
                    
                    with tab1:
                        st.line_chart(
                            crypto_data.set_index('timestamp')['Close'],
                            use_container_width=True
                        )
                    
                    # 获取新闻
                    news_list = get_crypto_news(crypto_name)
                    source_text = "来源" if get_language() == "zh" else "Source"
                    news_content = "\n".join([
                        f"- {item['title']} ({source_text}: {item['source']})"
                        for item in news_list
                    ]) if news_list else ("没有找到相关新闻。" if get_language() == "zh" else "No related news found.")
                    
                    # 存储数据供AI分析使用
                    st.session_state.crypto_data = crypto_data
                    st.session_state.news_content = news_content
                    st.session_state.news_list = news_list
                    st.session_state.show_analysis_button = True
                    
                    with tab2:
                        # 检查是否已经有数据
                        if 'crypto_data' not in st.session_state:
                            st.info("请先获取数据" if get_language() == "zh" else "Please fetch data first")
                        else:
                            with st.spinner("AI正在分析数据..." if get_language() == "zh" else "AI is analyzing data..."):
                                analysis = analyze_trend(
                                    st.session_state.crypto_data,
                                    crypto_name,
                                    period,
                                    st.session_state.news_content
                                )
                                st.markdown(analysis)
                    
                    with tab3:
                        if news_list:
                            for i, news in enumerate(news_list, 1):
                                with st.expander(f"{i}. {news['title']}", expanded=True):
                                    cols = st.columns([3, 2, 1])
                                    with cols[0]:
                                        source_text = "来源" if get_language() == "zh" else "Source"
                                        st.write(f"{source_text}: {news['source']}")
                                    with cols[1]:
                                        published_text = "发布时间" if get_language() == "zh" else "Published"
                                        st.write(f"{published_text}: {news['published']}")
                                    with cols[2]:
                                        read_more_text = "阅读原文" if get_language() == "zh" else "Read More"
                                        st.write(f"[{read_more_text}]({news['link']})")
                        else:
                            st.info("没有找到相关新闻" if get_language() == "zh" else "No related news found")
                else:
                    st.error(
                        "无法获取加密货币数据，请稍后重试。" if get_language() == "zh" else 
                        "Unable to fetch cryptocurrency data, please try again later."
                    )

if __name__ == "__main__":
    main()
