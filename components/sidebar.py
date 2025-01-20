import streamlit as st

def show_sidebar():
    # 添加自定义 CSS 来隐藏上方的导航栏
    st.markdown("""
        <style>
        [data-testid="stSidebarNav"] {display: none;}
        </style>
        """, unsafe_allow_html=True)
    
    st.sidebar.title("🧭 " + ("导航" if get_language() == "zh" else "Navigation"))
    
    with st.sidebar:
        st.title("金融数据分析" if get_language() == "zh" else "Financial Analysis")
        
        # 添加语言选择
        lang = st.selectbox(
            "语言 / Language",
            ["中文", "English"],
            index=0 if get_language() == "zh" else 1,
            key="language_selector"
        )
        # 更新语言设置
        st.session_state.language = "zh" if lang == "中文" else "en"
        
        # 添加页面导航
        st.subheader("📊 " + ("数据分析" if get_language() == "zh" else "Data Analysis"))
        if st.button("🏠 " + ("主页" if get_language() == "zh" else "Home"), key="home"):
            st.switch_page("app.py")
            
        if st.button("📈 " + ("股票分析" if get_language() == "zh" else "Stock Analysis"), key="stock"):
            st.switch_page("pages/stock_analysis.py")
            
        if st.button("💱 " + ("市场价格" if get_language() == "zh" else "Market Prices"), key="market"):
            st.switch_page("pages/market_prices.py")
            
        if st.button("📰 " + ("金融新闻" if get_language() == "zh" else "Financial News"), key="news"):
            st.switch_page("pages/financial_news.py")
        
        if st.button("💰 " + ("加密货币" if get_language() == "zh" else "Crypto"), key="crypto"):
            st.switch_page("pages/crypto_analysis.py")
        
        # 添加分隔线
        st.divider()
        
        # 添加设置按钮
        st.subheader("⚙️ " + ("设置" if get_language() == "zh" else "Settings"))
        if st.button("⚙️ " + ("系统设置" if get_language() == "zh" else "System Settings"), key="settings"):
            st.switch_page("pages/settings.py")
        
        # 添加底部信息
        st.sidebar.markdown("---")
        st.sidebar.caption("© 2024 " + ("金融数据分析平台" if get_language() == "zh" else "Financial Analysis Platform"))
        
        # 添加分隔线
        st.sidebar.divider()
        
        # 添加清空缓存按钮
        if st.sidebar.button(
            "🗑️ " + ("清空缓存" if get_language() == "zh" else "Clear Cache"),
            help=("清除所有缓存的分析结果和临时数据" if get_language() == "zh" 
                  else "Clear all cached analysis results and temporary data")
        ):
            # 清除session_state中的缓存数据
            keys_to_keep = {'language', 'ai_model', 'openai_api_key', 'config_loaded'}
            for key in list(st.session_state.keys()):
                if key not in keys_to_keep:
                    del st.session_state[key]
            
            st.sidebar.success(
                "缓存已清空！" if get_language() == "zh" else "Cache cleared!"
            )
            
            # 重新加载页面
            st.rerun()

def get_language():
    """获取当前语言设置"""
    if 'language' not in st.session_state:
        st.session_state.language = "zh"
    return st.session_state.language