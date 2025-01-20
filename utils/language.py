import streamlit as st

def get_language():
    """获取当前语言设置"""
    return st.session_state.get('language', 'zh')