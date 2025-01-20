import streamlit as st
from components.sidebar import show_sidebar, get_language
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
import os
from dotenv import load_dotenv
from pages.financial_news import get_financial_news
from utils.config import load_config
import urllib.parse
import feedparser
import requests

# 加载环境变量
load_dotenv()

# 加载配置
if 'config_loaded' not in st.session_state:
    config = load_config()
    st.session_state.language = config['language']
    st.session_state.ai_model = config['ai_model']
    st.session_state.config_loaded = True

# 初始化 ChatOpenAI
llm = ChatOpenAI(
    model=st.session_state.get('ai_model', 'o1-mini')
)

# 检查并清理过期缓存
def clear_expired_cache():
    """每天凌晨清理缓存"""
    now = datetime.now()
    last_clear = st.session_state.get('last_cache_clear')
    
    if last_clear is None or (now.date() > last_clear.date()):
        # 清理所有缓存的分析结果
        keys_to_clear = [k for k in st.session_state.keys() if k.startswith('analysis_') or k.startswith('technical_')]
        for key in keys_to_clear:
            del st.session_state[key]
        st.session_state['last_cache_clear'] = now

# 设置页面配置
st.set_page_config(
    page_title="股票分析" if get_language() == "zh" else "Stock Analysis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 显示侧边栏
show_sidebar()

# 设置页面标题
st.title("📈 " + ("股票分析" if get_language() == "zh" else "Stock Analysis"))

# 加载股票数据
@st.cache_data
def load_stock_data():
    df = pd.read_csv('wiki_stocks.csv')
    # 创建一个字典，key是公司名称，value是股票代码
    return {f"{row['name']} ({row['code']})": row['code'] for _, row in df.iterrows()}

# 创建股票选择器
stock_dict = load_stock_data()


# 添加缓存状态显示
def show_cache_status(ticker):
    """显示数据缓存状态"""
    if st.session_state.get(f'last_update_{ticker}'):
        last_update = st.session_state[f'last_update_{ticker}']
        st.sidebar.info(f"数据最后更新时间: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")
        time_diff = datetime.now() - last_update
        hours_left = 24 - (time_diff.total_seconds() / 3600)
        if hours_left > 0:
            st.sidebar.info(f"缓存将在 {hours_left:.1f} 小时后过期")

# 使用缓存装饰器，设置TTL为24小时
@st.cache_data(ttl=timedelta(hours=24))
def get_stock_data(ticker, period="1mo"):
    """获取股票数据，带有24小时缓存"""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period)
        return data
    except Exception as e:
        st.error(f"获取股票数据时出错: {str(e)}")
        return None

@st.cache_data(ttl=timedelta(hours=24))
def get_company_info(ticker):
    """获取公司信息，带有24小时缓存"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        company_data = {
            "公司名称": info.get('longName', '未知'),
            "行业": info.get('industry', '未知'),
            "板块": info.get('sector', '未知'),
            "市值": f"{info.get('marketCap', 0) / 100000000:.2f}亿",
            "市盈率(TTM)": f"{info.get('trailingPE', 0):.2f}",
            "市净率": f"{info.get('priceToBook', 0):.2f}",
            "52周最高": info.get('fiftyTwoWeekHigh', '未知'),
            "52周最低": info.get('fiftyTwoWeekLow', '未知'),
            "每股收益(TTM)": info.get('trailingEps', '未知'),
            "股息率": f"{info.get('dividendYield', 0) * 100:.2f}%" if info.get('dividendYield') else '未知',
            "公司简介": info.get('longBusinessSummary', '未知')
        }
        
        financials = stock.financials
        balance_sheet = stock.balance_sheet
        cash_flow = stock.cashflow
        
        return company_data, financials, balance_sheet, cash_flow
    except Exception as e:
        st.error(f"获取公司信息时出错: {str(e)}")
        return None, None, None, None

@st.cache_data(ttl=timedelta(hours=24))
def calculate_technical_indicators(data):
    """计算技术指标，带有24小时缓存"""
    try:
        df = data.copy()
        
        # 计算移动平均线
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA10'] = df['Close'].rolling(window=10).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()
        
        # 计算MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_SIGNAL'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_HIST'] = df['MACD'] - df['MACD_SIGNAL']
        
        # 计算RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # 计算KDJ
        low_min = df['Low'].rolling(window=9).min()
        high_max = df['High'].rolling(window=9).max()
        rsv = (df['Close'] - low_min) / (high_max - low_min) * 100
        df['K'] = rsv.rolling(window=3).mean()
        df['D'] = df['K'].rolling(window=3).mean()
        df['J'] = 3 * df['K'] - 2 * df['D']
        
        # 计算布林带
        df['BOLL_MIDDLE'] = df['Close'].rolling(window=20).mean()
        std = df['Close'].rolling(window=20).std()
        df['BOLL_UPPER'] = df['BOLL_MIDDLE'] + 2 * std
        df['BOLL_LOWER'] = df['BOLL_MIDDLE'] - 2 * std
        
        # 计算成交量均线
        df['VOLUME_MA5'] = df['Volume'].rolling(window=5).mean()
        df['VOLUME_MA10'] = df['Volume'].rolling(window=10).mean()
        
        return df
    except Exception as e:
        st.error(f"计算技术指标时出错: {str(e)}")
        return None

def get_stock_news(stock_name, num_news=20):
    """根据股票名称获取最近一周的新闻"""
    try:
        # URL编码股票名称
        encoded_stock_name = urllib.parse.quote(stock_name)
        
        # 正确的 Google News RSS URL
        rss_url = f"https://news.google.com/rss/search?q={encoded_stock_name}+when:7d&hl=zh-CN&gl=CN&ceid=CN:zh-CN"
        
        # 解析 RSS feed
        feed = feedparser.parse(rss_url)
        
        # 检查是否成功获取新闻
        if not feed.entries:
            return []
        
        # 提取新闻
        news_list = []
        # 确保使用默认的整数值
        max_news = 20  # 固定获取5条新闻
        
        for entry in feed.entries:
            if len(news_list) >= max_news:  # 当达到所需数量时退出循环
                break
                
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

def load_api_key():
    """加载 OpenAI API Key"""
    if 'openai_api_key' not in st.session_state:
        # 尝试从环境变量加载 API Key
        st.session_state['openai_api_key'] = os.getenv("OPENAI_API_KEY", "")
    
    # 如果 API Key 为空，提示用户输入
    if not st.session_state['openai_api_key']:
        st.session_state['openai_api_key'] = st.text_input("请输入 OpenAI API Key", type="password")

def save_api_key(api_key):
    """保存 OpenAI API Key"""
    st.session_state['openai_api_key'] = api_key
    # 这里可以选择将 API Key 保存到环境变量或配置文件中
    os.environ["OPENAI_API_KEY"] = api_key  # 仅在当前会话中有效

# 在页面加载时加载 API Key
load_api_key()

def analyze_trend(stock_data, stock_name, period, company_data, financials, news_content):
    """使用LangChain和OpenAI分析股票趋势"""
    try:
        cache_key = f'analysis_{stock_name}_{period}_{get_language()}'
        if cache_key in st.session_state:
            return st.session_state[cache_key]
        
        # 检查是否设置了 API Key
        api_key = st.session_state.get('openai_api_key')
        if not api_key:
            return ("请在设置页面配置 OpenAI API Key" if get_language() == "zh" 
                   else "Please configure OpenAI API Key in settings")
        
        # 使用配置的 API Key
        os.environ["OPENAI_API_KEY"] = api_key  # 确保 API Key 被设置
        
        # 使用配置的模型
        model = st.session_state.get('ai_model', 'gpt-3.5-turbo')
        llm = ChatOpenAI(model=model)
        
        with st.spinner(
            '正在生成分析报告...' if get_language() == "zh" else 'Generating analysis...'
        ):
            latest_price = stock_data['Close'].iloc[-1]
            price_change = (latest_price - stock_data['Close'].iloc[0]) / stock_data['Close'].iloc[0] * 100
            avg_volume = stock_data['Volume'].mean()
            
            # 根据当前语言选择提示词
            if get_language() == "zh":
                prompt = f"""
                请分析以下股票数据并生成详细报告：

                股票：{stock_name}
                当前价格：${latest_price:.2f}
                期间涨跌幅：{price_change:.2f}%
                平均成交量：{avg_volume:,.0f}
                行业：{company_data.get('行业' if get_language() == 'zh' else 'Industry', '未知')}
                市值：{company_data.get('市值' if get_language() == 'zh' else 'Market Cap', '未知')}
                市盈率：{company_data.get('市盈率(TTM)' if get_language() == 'zh' else 'P/E Ratio(TTM)', '未知')}

                相关新闻：
                {news_content}

                请提供以下方面的分析：
                1. 价格趋势分析
                2. 成交量分析
                3. 基本面分析
                4. 相关新闻分析
                5. 投资建议

                请用中文回答，并使用markdown格式。
                """
            else:
                prompt = f"""
                Please analyze the following stock data and generate a detailed report:

                Stock: {stock_name}
                Current Price: ${latest_price:.2f}
                Period Change: {price_change:.2f}%
                Average Volume: {avg_volume:,.0f}
                Industry: {company_data.get('Industry', 'Unknown')}
                Market Cap: {company_data.get('Market Cap', 'Unknown')}
                P/E Ratio: {company_data.get('P/E Ratio(TTM)', 'Unknown')}

                Related News:
                {news_content}

                Please provide analysis on:
                1. Price Trend Analysis
                2. Volume Analysis
                3. Fundamental Analysis
                4. Related News Analysis
                5. Investment Recommendations

                Please respond in English using markdown format.
                """
            
            analysis = llm.invoke(prompt)
            analysis_content = analysis.content if hasattr(analysis, 'content') else str(analysis)
            st.session_state[cache_key] = analysis_content
            return analysis_content
            
    except Exception as e:
        return (
            f"生成分析报告时出错: {str(e)}" if get_language() == "zh" 
            else f"Error generating analysis: {str(e)}"
        )

def analyze_technical_indicators(tech_data, stock_name):
    """使用LangChain和OpenAI分析技术指标"""
    try:
        current_date = datetime.now().strftime('%Y-%m-%d')
        cache_key = f'technical_{stock_name}_{current_date}_{get_language()}'
        
        if cache_key in st.session_state:
            return st.session_state[cache_key]
        
                # 检查是否设置了 API Key
        api_key = st.session_state.get('openai_api_key')
        if not api_key:
            return ("请在设置页面配置 OpenAI API Key" if get_language() == "zh" 
                   else "Please configure OpenAI API Key in settings")
        
        with st.spinner(
            '正在生成技术分析...' if get_language() == "zh" else 'Generating technical analysis...'
        ):
            latest = tech_data.iloc[-1]
            
            # 根据当前语言选择提示词
            if get_language() == "zh":
                prompt = f"""
                请分析以下股票的技术指标并生成详细报告：

                股票：{stock_name}

                技术指标数据：
                MACD：{latest['MACD']:.3f}
                MACD信号线：{latest['MACD_SIGNAL']:.3f}
                RSI：{latest['RSI']:.2f}
                布林带上轨：{latest['BOLL_UPPER']:.2f}
                布林带中轨：{latest['BOLL_MIDDLE']:.2f}
                布林带下轨：{latest['BOLL_LOWER']:.2f}

                请提供以下分析：
                1. MACD分析
                2. RSI分析
                3. 布林带分析
                4. 综合建议

                请用中文回答，并使用markdown格式。
                """
            else:
                prompt = f"""
                Please analyze the following technical indicators and generate a detailed report:

                Stock: {stock_name}

                Technical Indicators:
                MACD: {latest['MACD']:.3f}
                MACD Signal: {latest['MACD_SIGNAL']:.3f}
                RSI: {latest['RSI']:.2f}
                Bollinger Upper: {latest['BOLL_UPPER']:.2f}
                Bollinger Middle: {latest['BOLL_MIDDLE']:.2f}
                Bollinger Lower: {latest['BOLL_LOWER']:.2f}

                Please provide analysis on:
                1. MACD Analysis
                2. RSI Analysis
                3. Bollinger Bands Analysis
                4. Overall Recommendations

                Please respond in English using markdown format.
                """
            
            analysis = llm.invoke(prompt)
            analysis_content = analysis.content if hasattr(analysis, 'content') else str(analysis)
            st.session_state[cache_key] = analysis_content
            return analysis_content
            
    except Exception as e:
        return (
            f"生成技术分析报告时出错: {str(e)}" if get_language() == "zh" 
            else f"Error generating technical analysis: {str(e)}"
        )

# 在页面加载时检查并清理过期缓存
clear_expired_cache()

# 添加手动刷新按钮
def add_refresh_button(stock_name, period):
    if st.button("🔄 刷新分析", key=f"refresh_{stock_name}_{period}"):
        # 清除该股票和时间区间的缓存
        keys_to_clear = [
            k for k in st.session_state.keys() 
            if (k.startswith(f'analysis_{stock_name}_{period}') or 
                k.startswith(f'technical_{stock_name}'))
        ]
        for key in keys_to_clear:
            del st.session_state[key]
        st.success("分析已刷新！")
        st.rerun()

st.title("股票分析")
load_api_key()

# 使用容器来控制内容宽度
with st.container():
    selected_stock = st.selectbox(
        "选择股票" if get_language() == "zh" else "Select Stock",
        list(stock_dict.keys())
    )
    

if selected_stock:
    period = st.selectbox(
        "选择时间范围" if get_language() == "zh" else "Select Time Range",
        ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"],
        index=2
    )
    add_refresh_button(selected_stock, period)
    
    # 获取股票代码
    ticker = stock_dict[selected_stock]
    
    with st.spinner('正在加载股票数据...'):
        # 显示缓存状态
        show_cache_status(ticker)
        
        # 获取数据（使用缓存）
        stock_data = get_stock_data(ticker, period)
        company_data, financials, balance_sheet, cash_flow = get_company_info(ticker)
        
        # 更新最后更新时间
        if stock_data is not None:
            st.session_state[f'last_update_{ticker}'] = datetime.now()
    
    # 创建标签页
    tab_names = ["公司信息", "价格走势", "相关新闻", "AI分析", "技术指标"] if get_language() == "zh" else \
                ["Company Info", "Price Trend", "Related News", "AI Analysis", "Technical Indicators"]
    info_tab, chart_tab, news_tab, analysis_tab, technical_tab = st.tabs(tab_names)
    
    with info_tab:
        with st.spinner('正在加载公司信息...' if get_language() == "zh" else 'Loading company information...'):
            if company_data:
                # 显示公司基本信息
                st.subheader("公司基本信息" if get_language() == "zh" else "Company Information")
                
                # 定义翻译字典
                key_trans = {
                    '公司名称': 'Company Name',
                    '行业': 'Industry',
                    '板块': 'Sector',
                    '市值': 'Market Cap',
                    '市盈率(TTM)': 'P/E Ratio(TTM)',
                    '每股收益(TTM)': 'EPS(TTM)',
                    '市净率': 'P/B Ratio',
                    '股息率': 'Dividend Yield',
                    '52周最高': '52 Week High',
                    '52周最低': '52 Week Low',
                    '公司简介': 'Company Profile',
                }
                
                # 未知值的翻译
                unknown_text = "未知" if get_language() == "zh" else "Unknown"
                
                # 基本信息列
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("基本信息" if get_language() == "zh" else "Basic Information")
                    basic_info = {
                        '公司名称': company_data.get('公司名称', unknown_text),
                        '行业': company_data.get('行业', unknown_text),
                        '板块': company_data.get('板块', unknown_text),
                        '市值': company_data.get('市值', unknown_text),
                        '市盈率(TTM)': company_data.get('市盈率(TTM)', unknown_text)
                    }
                    
                    for key, value in basic_info.items():
                        display_key = key_trans.get(key, key) if get_language() == "en" else key
                        # 如果值是"未知"，翻译它
                        display_value = unknown_text if value == "未知" else value
                        st.write(f"**{display_key}:** {display_value}")
                
                # 市场数据列
                with col2:
                    market_metrics = {
                        '市净率': company_data.get('市净率', unknown_text),
                        '每股收益(TTM)': company_data.get('每股收益(TTM)', unknown_text),
                        '股息率': company_data.get('股息率', unknown_text),
                        '52周最高': company_data.get('52周最高', unknown_text),
                        '52周最低': company_data.get('52周最低', unknown_text)
                    }
                    
                    for key, value in market_metrics.items():
                        display_key = key_trans.get(key, key) if get_language() == "en" else key
                        # 如果值是"未知"，翻译它
                        display_value = unknown_text if value == "未知" else value
                        st.metric(display_key, display_value)
                
                # 显示公司简介
                st.subheader("公司简介" if get_language() == "zh" else "Company Profile")
                company_profile = company_data.get('公司简介', unknown_text)
                # 如果简介是"未知"，翻译它
                display_profile = unknown_text if company_profile == "未知" else company_profile
                st.write(display_profile)
                
                # 显示财务报表
                st.subheader("财务报表" if get_language() == "zh" else "Financial Statements")
                tabs = st.tabs([
                    "利润表" if get_language() == "zh" else "Income Statement",
                    "资产负债表" if get_language() == "zh" else "Balance Sheet",
                    "现金流量表" if get_language() == "zh" else "Cash Flow Statement"
                ])
                
                with tabs[0]:
                    if financials is not None and not financials.empty:
                        st.dataframe(financials.style.format("{:,.2f}"))
                    else:
                        st.write("暂无利润表数据" if get_language() == "zh" else "No income statement data available")
                
                with tabs[1]:
                    if balance_sheet is not None and not balance_sheet.empty:
                        st.dataframe(balance_sheet.style.format("{:,.2f}"))
                    else:
                        st.write("暂无资产负债表数据" if get_language() == "zh" else "No balance sheet data available")
                
                with tabs[2]:
                    if cash_flow is not None and not cash_flow.empty:
                        st.dataframe(cash_flow.style.format("{:,.2f}"))
                    else:
                        st.write("暂无现金流量表数据" if get_language() == "zh" else "No cash flow data available")
    

    with news_tab:
        st.subheader("🔍 " + ("相关新闻" if get_language() == "zh" else "Related News"))
        news_list = get_stock_news(selected_stock, period)
        if isinstance(news_list, str):
            st.error(news_list)  # 如果返回的是错误信息，显示错误
        else:
            for news in news_list:
                st.write(news['title'])
                st.link_button("阅读原文", news['link'])
                st.write(news['published'])
                st.write(news['source'])

    
    with chart_tab:
        with st.spinner('正在生成价格走势图...' if get_language() == "zh" else 'Generating price chart...'):
            # 获取股票数据
            stock_data = get_stock_data(ticker, period)
            
            if stock_data is not None:
                # 显示股票价格走势图
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=stock_data.index,
                    y=stock_data['Close'],
                    name=('收盘价' if get_language() == "zh" else 'Close Price')
                ))
                fig.update_layout(
                    title=f'{selected_stock} ' + ('价格走势' if get_language() == "zh" else 'Price Trend'),
                    yaxis_title=('价格' if get_language() == "zh" else 'Price'),
                    template='plotly_dark'
                )
                st.plotly_chart(fig)
                
                # 显示成交量图
                volume_fig = go.Figure()
                volume_fig.add_trace(go.Bar(
                    x=stock_data.index,
                    y=stock_data['Volume'],
                    name=('成交量' if get_language() == "zh" else 'Volume')
                ))
                volume_fig.update_layout(
                    title=('成交量' if get_language() == "zh" else 'Volume'),
                    yaxis_title=('成交量' if get_language() == "zh" else 'Volume'),
                    template='plotly_dark'
                )
                st.plotly_chart(volume_fig)
    
    with analysis_tab:
        st.subheader("🤖 " + ("AI 分析" if get_language() == "zh" else "AI Analysis"))
        news_list = get_stock_news(selected_stock, period)
        if isinstance(news_list, str):
            st.error(news_list)  # 如果返回的是错误信息，显示错误
        else:
            news_content = "\n".join([f"- {item['title']} (来源: {item['source']})" for item in news_list if isinstance(item, dict)]) if news_list else "没有找到相关新闻。"
            analysis_text = analyze_trend(stock_data, selected_stock, period, company_data, financials, news_content)
            st.markdown(analysis_text)
        
        # 添加复制按钮
        if st.button("📋 " + ("复制分析" if get_language() == "zh" else "Copy Analysis")):
            st.toast("分析已复制到剪贴板！" if get_language() == "zh" else "Analysis copied to clipboard!")
            st.clipboard_copy(analysis_text)

    # 计算技术指标
    tech_data = calculate_technical_indicators(stock_data)
    
    with technical_tab:
        st.subheader("📊 " + ("技术指标分析" if get_language() == "zh" else "Technical Analysis"))
        
        # MACD图表
        fig_macd = go.Figure()
        fig_macd.add_trace(go.Scatter(x=tech_data.index, y=tech_data['MACD'], name='MACD'))
        fig_macd.add_trace(go.Scatter(x=tech_data.index, y=tech_data['MACD_SIGNAL'], name='Signal Line'))
        fig_macd.update_layout(
            title='MACD',
            yaxis_title='MACD',
            template='plotly_dark'
        )
        st.plotly_chart(fig_macd)

        # RSI图表
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=tech_data.index, y=tech_data['RSI'], name='RSI'))
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
        fig_rsi.update_layout(
            title='RSI',
            yaxis_title='RSI',
            template='plotly_dark'
        )
        st.plotly_chart(fig_rsi)

        # 布林带图表
        fig_boll = go.Figure()
        fig_boll.add_trace(go.Scatter(x=tech_data.index, y=tech_data['BOLL_UPPER'], name='Upper Band'))
        fig_boll.add_trace(go.Scatter(x=tech_data.index, y=tech_data['BOLL_MIDDLE'], name='Middle Band'))
        fig_boll.add_trace(go.Scatter(x=tech_data.index, y=tech_data['BOLL_LOWER'], name='Lower Band'))
        fig_boll.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Close'], name='Close Price'))
        fig_boll.update_layout(
            title='Bollinger Bands',
            yaxis_title='Price',
            template='plotly_dark'
        )
        st.plotly_chart(fig_boll)

        # AI分析
        tech_analysis = analyze_technical_indicators(tech_data, selected_stock)
        st.markdown(tech_analysis)
        
        # 添加复制按钮
        if st.button("📋 " + ("复制技术分析" if get_language() == "zh" else "Copy Technical Analysis")):
            st.toast("技术分析已复制到剪贴板！" if get_language() == "zh" else "Technical analysis copied to clipboard!")
            st.clipboard_copy(tech_analysis)

# 添加刷新按钮
if st.button('🔄 ' + ("刷新数据" if get_language() == "zh" else "Refresh Data")):
    st.rerun()

# 显示最后更新时间
st.text(("最后更新时间: " if get_language() == "zh" else "Last Updated: ") + 
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')) 

# 图表标题和标签
def create_price_chart(data):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name=("价格" if get_language() == "zh" else "Price")
    ))
    
    fig.update_layout(
        title=("股票价格走势" if get_language() == "zh" else "Stock Price Trend"),
        yaxis_title=("价格" if get_language() == "zh" else "Price"),
        xaxis_title=("日期" if get_language() == "zh" else "Date"),
        template='plotly_dark'
    )
    return fig

def create_macd_chart(data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data.index, 
        y=data['MACD'], 
        name='MACD'
    ))
    fig.add_trace(go.Scatter(
        x=data.index, 
        y=data['MACD_SIGNAL'], 
        name=("信号线" if get_language() == "zh" else "Signal Line")
    ))
    
    fig.update_layout(
        title='MACD',
        yaxis_title='MACD',
        xaxis_title=("日期" if get_language() == "zh" else "Date"),
        template='plotly_dark'
    )
    return fig

def create_rsi_chart(data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data.index, 
        y=data['RSI'], 
        name='RSI'
    ))
    fig.add_hline(
        y=70, 
        line_dash="dash", 
        line_color="red", 
        annotation_text=("超买" if get_language() == "zh" else "Overbought")
    )
    fig.add_hline(
        y=30, 
        line_dash="dash", 
        line_color="green", 
        annotation_text=("超卖" if get_language() == "zh" else "Oversold")
    )
    
    fig.update_layout(
        title='RSI',
        yaxis_title='RSI',
        xaxis_title=("日期" if get_language() == "zh" else "Date"),
        template='plotly_dark'
    )
    return fig

def create_bollinger_chart(data, stock_data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data.index, 
        y=data['BOLL_UPPER'], 
        name=("上轨" if get_language() == "zh" else "Upper Band")
    ))
    fig.add_trace(go.Scatter(
        x=data.index, 
        y=data['BOLL_MIDDLE'], 
        name=("中轨" if get_language() == "zh" else "Middle Band")
    ))
    fig.add_trace(go.Scatter(
        x=data.index, 
        y=data['BOLL_LOWER'], 
        name=("下轨" if get_language() == "zh" else "Lower Band")
    ))
    fig.add_trace(go.Scatter(
        x=stock_data.index, 
        y=stock_data['Close'], 
        name=("收盘价" if get_language() == "zh" else "Close Price")
    ))
    
    fig.update_layout(
        title=("布林带" if get_language() == "zh" else "Bollinger Bands"),
        yaxis_title=("价格" if get_language() == "zh" else "Price"),
        xaxis_title=("日期" if get_language() == "zh" else "Date"),
        template='plotly_dark'
    )
    return fig 

# 示例按钮，保存 API Key
if st.button("保存 API Key"):
    save_api_key(st.session_state['openai_api_key'])
    st.success("API Key 已保存！")

