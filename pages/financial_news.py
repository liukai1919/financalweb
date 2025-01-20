import streamlit as st
import feedparser
from datetime import datetime, timedelta
from components.sidebar import show_sidebar, get_language
from langchain_openai import ChatOpenAI
import urllib.parse

# 设置页面配置
st.set_page_config(
    page_title="金融新闻" if get_language() == "zh" else "Financial News",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 显示侧边栏
show_sidebar()

# 初始化 ChatOpenAI
llm = ChatOpenAI(
    model="o1-mini"
)

def get_financial_news(topic, num_news=20):
    """获取金融新闻"""
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

def analyze_news(news_list, topic):
    """使用AI分析新闻趋势"""
    try:
        if not news_list or isinstance(news_list, str):
            return "暂无相关新闻可供分析" if get_language() == "zh" else "No news available for analysis"
            
        with st.spinner('正在分析相关新闻...' if get_language() == "zh" else 'Analyzing news...'):
            titles = [news['title'] for news in news_list if isinstance(news, dict) and 'title' in news]
            
            if not titles:
                return "暂无有效新闻可供分析" if get_language() == "zh" else "No valid news available for analysis"
                
            titles_text = "\n".join([f"- {title}" for title in titles])
            
            # 根据语言选择提示词
            if get_language() == "zh":
                prompt = f"""
                请分析以下{topic}相关的新闻标题，总结当前市场的主要关注点和趋势：

                新闻标题：
                {titles_text}

                请从以下几个方面进行分析：
                1. 主要市场动态
                2. 市场情绪倾向
                3. 潜在影响因素
                4. 需要关注的风险点

                要求：
                - 分析要简明扼要，突出重点
                - 注意新闻之间的关联性
                - 使用中文回答，语言专业清晰
                """
            else:
                prompt = f"""
                Please analyze the following news headlines related to {topic} and summarize the main market focus and trends:

                Headlines:
                {titles_text}

                Please analyze from the following aspects:
                1. Main Market Dynamics
                2. Market Sentiment
                3. Potential Impact Factors
                4. Risk Points to Watch

                Requirements:
                - Keep the analysis concise and focused
                - Note the connections between news items
                - Use professional and clear language
                """
            
            analysis = llm.invoke(prompt)
            return analysis.content if hasattr(analysis, 'content') else str(analysis)
            
    except Exception as e:
        error_msg = f"分析新闻时出错: {str(e)}" if get_language() == "zh" else f"Error analyzing news: {str(e)}"
        return error_msg

# 页面标题
st.title("📈 " + ("金融新闻" if get_language() == "zh" else "Financial News"))

# 创建新闻分类标签页
tabs_zh = ["全球市场", "美股市场", "A股市场", "外汇市场", "商品市场", "加密货币"]
tabs_en = ["Global Market", "US Market", "China Market", "Forex", "Commodities", "Crypto"]
tabs = tabs_zh if get_language() == "zh" else tabs_en

news_tabs = st.tabs(tabs)

with news_tabs[0]:
    with st.spinner('正在加载全球市场新闻...'):
        news = get_financial_news("global financial market stock")
        col1, col2 = st.columns([2, 1])
        with col1:
            if news:  # 检查是否有新闻
                for item in news:
                    with st.expander(f"📄 {item['title']}", expanded=False):
                        st.write(f"📅 发布时间: {item['published']}")
                        st.write(f"📰 来源: {item['source']}")
                        st.link_button("🔗 阅读全文", item['link'])
            else:
                st.write("没有找到最近一周的新闻。")  # 提示没有新闻

        with col2:
            with st.expander("🤖 AI分析", expanded=True):
                if st.button("生成分析", key="global_analysis"):
                    analysis = analyze_news(news, "全球市场")
                    st.write(analysis)

with news_tabs[1]:
    with st.spinner('正在加载美股市场新闻...'):
        news = get_financial_news("US stock market NYSE NASDAQ")
        col1, col2 = st.columns([2, 1])
        with col1:
            for item in news:
                with st.expander(f"📄 {item['title']}", expanded=False):
                    st.write(f"📅 发布时间: {item['published']}")
                    st.write(f"📰 来源: {item['source']}")
                    st.link_button("🔗 阅读全文", item['link'])
        with col2:
            with st.expander("🤖 AI分析", expanded=True):
                if st.button("生成分析", key="us_analysis"):
                    analysis = analyze_news(news, "美股市场")
                    st.write(analysis)

with news_tabs[2]:
    with st.spinner('正在加载A股市场新闻...'):
        news = get_financial_news("A股市场 上证指数 创业板")
        col1, col2 = st.columns([2, 1])
        with col1:
            for item in news:
                with st.expander(f"📄 {item['title']}", expanded=False):
                    st.write(f"📅 发布时间: {item['published']}")
                    st.write(f"📰 来源: {item['source']}")
                    st.link_button("🔗 阅读全文", item['link'])
        with col2:
            with st.expander("🤖 AI分析", expanded=True):
                if st.button("生成分析", key="a_share_analysis"):
                    analysis = analyze_news(news, "A股市场")
                    st.write(analysis)

with news_tabs[3]:
    with st.spinner('正在加载外汇市场新闻...'):
        news = get_financial_news("外汇市场 人民币 汇率")
        col1, col2 = st.columns([2, 1])
        with col1:
            for item in news:
                with st.expander(f"📄 {item['title']}", expanded=False):
                    st.write(f"📅 发布时间: {item['published']}")
                    st.write(f"📰 来源: {item['source']}")
                    st.link_button("🔗 阅读全文", item['link'])
        with col2:
            with st.expander("🤖 AI分析", expanded=True):
                if st.button("生成分析", key="forex_analysis"):
                    analysis = analyze_news(news, "外汇市场")
                    st.write(analysis)

with news_tabs[4]:
    with st.spinner('正在加载商品市场新闻...'):
        news = get_financial_news("大宗商品 黄金 原油")
        col1, col2 = st.columns([2, 1])
        with col1:
            for item in news:
                with st.expander(f"📄 {item['title']}", expanded=False):
                    st.write(f"📅 发布时间: {item['published']}")
                    st.write(f"📰 来源: {item['source']}")
                    st.link_button("🔗 阅读全文", item['link'])
        with col2:
            with st.expander("🤖 AI分析", expanded=True):
                if st.button("生成分析", key="commodity_analysis"):
                    analysis = analyze_news(news, "商品市场")
                    st.write(analysis)

with news_tabs[5]:
    with st.spinner('正在加载加密货币新闻...'):
        news = get_financial_news("比特币 加密货币")
        col1, col2 = st.columns([2, 1])
        with col1:
            for item in news:
                with st.expander(f"📄 {item['title']}", expanded=False):
                    st.write(f"📅 发布时间: {item['published']}")
                    st.write(f"📰 来源: {item['source']}")
                    st.link_button("🔗 阅读全文", item['link'])
        with col2:
            with st.expander("🤖 AI分析", expanded=True):
                if st.button("生成分析", key="crypto_analysis"):
                    analysis = analyze_news(news, "加密货币市场")
                    st.write(analysis)

# 添加刷新按钮
if st.button('🔄 ' + ("刷新新闻" if get_language() == "zh" else "Refresh News")):
    st.rerun()

# 显示最后更新时间
update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
st.text(("最后更新时间: " if get_language() == "zh" else "Last Updated: ") + update_time)

