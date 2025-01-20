import streamlit as st
from utils.config import load_config, save_config, clear_config
from utils.language import get_language
from components.sidebar import show_sidebar
import os

# 显示侧边栏
show_sidebar()

st.title("⚙️ " + ("系统设置" if get_language() == "zh" else "Settings"))

# 加载当前配置
current_config = load_config()

# 如果是保存后的状态，使用session_state中的新值
if 'new_settings_saved' in st.session_state:
    current_config = st.session_state.new_settings_saved
    del st.session_state.new_settings_saved

col1, col2 = st.columns(2)

with col1:
    st.subheader("🌐 " + ("语言设置" if get_language() == "zh" else "Language Settings"))
    
    # 语言选择
    language_options = {
        "zh": "中文",
        "en": "English"
    }
    
    selected_language = st.selectbox(
        ("语言" if get_language() == "zh" else "Language"),
        options=list(language_options.keys()),
        format_func=lambda x: language_options[x],
        index=list(language_options.keys()).index(current_config.get('language', 'zh')),
        key="temp_language"
    )

with col2:
    st.subheader("🎨 " + ("界面设置" if get_language() == "zh" else "Interface Settings"))
    
    # 主题选择
    theme_options = {
        "dark": "深色" if get_language() == "zh" else "Dark",
        "light": "浅色" if get_language() == "zh" else "Light"
    }
    
    selected_theme = st.selectbox(
        ("主题" if get_language() == "zh" else "Theme"),
        options=list(theme_options.keys()),
        format_func=lambda x: theme_options[x],
        index=list(theme_options.keys()).index(current_config.get('theme', 'dark')),
        key="temp_theme"
    )

st.subheader("🤖 " + ("AI设置" if get_language() == "zh" else "AI Settings"))

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

# 在应用启动时加载 API Key
load_api_key()

# OpenAI API Key 设置
api_key = st.text_input(
    "OpenAI API Key",
    type="password",
    value=current_config.get('openai_api_key', ''),
    key="temp_api_key",
    help=("请输入您的 OpenAI API Key。该密钥将被安全存储在本地配置文件中。" if get_language() == "zh" 
          else "Please enter your OpenAI API Key. The key will be stored securely in local config file.")
)

# AI 模型选择
model_options = [
    "gpt-3.5-turbo",
    "gpt-4",
    "gpt-4-0125-preview",  # 最新稳定版
    "gpt-4-turbo-preview",  # 最新预览版
    "gpt-4o",               # GPT-4o
    "gpt-4o-mini",          # GPT-4o-mini
    "o1-mini"               # o1-mini
]

model_descriptions = {
    "gpt-3.5-turbo": "GPT-3.5 Turbo - " + ("快速且经济" if get_language() == "zh" else "Fast and Economic"),
    "gpt-4": "GPT-4 - " + ("基础稳定版" if get_language() == "zh" else "Base Stable Version"),
    "gpt-4-0125-preview": "GPT-4 (0125) - " + ("最新稳定版" if get_language() == "zh" else "Latest Stable Version"),
    "gpt-4-turbo-preview": "GPT-4 Turbo - " + ("预览版" if get_language() == "zh" else "Preview Version"),
    "gpt-4o": "GPT-4o - " + ("优化版" if get_language() == "zh" else "Optimized Version"),
    "gpt-4o-mini": "GPT-4o-mini - " + ("轻量版" if get_language() == "zh" else "Lightweight Version"),
    "o1-mini": "o1-mini - " + ("轻量版" if get_language() == "zh" else "Lightweight Version")
}

selected_model = st.selectbox(
    ("AI模型" if get_language() == "zh" else "AI Model"),
    options=model_options,
    format_func=lambda x: model_descriptions[x],
    index=model_options.index(current_config.get('ai_model', 'gpt-3.5-turbo')),
    key="temp_model",
    help=("选择要使用的AI模型。不同模型有不同的特点和定价。" if get_language() == "zh" 
          else "Select the AI model to use. Different models have different capabilities and pricing.")
)

# 添加保存按钮
if st.button("💾 " + ("保存设置" if get_language() == "zh" else "Save Settings")):
    # 准备新的配置
    new_config = {
        'language': selected_language,
        'theme': selected_theme,
        'openai_api_key': api_key,
        'ai_model': selected_model
    }
    
    # 检查配置是否有变化
    if new_config != current_config:
        if save_config(new_config):
            # 立即更新 session_state
            for key, value in new_config.items():
                st.session_state[key] = value
            
            # 如果主题改变，立即更新配置文件
            if new_config['theme'] != current_config.get('theme'):
                with open('.streamlit/config.toml', 'r') as f:
                    config_content = f.read()
                
                # 替换主题设置
                config_content = '\n'.join([
                    line if not line.strip().startswith('base') 
                    else f'base = "{selected_theme}"' 
                    for line in config_content.splitlines()
                ])
                
                with open('.streamlit/config.toml', 'w') as f:
                    f.write(config_content)
            
            st.success(
                "设置已保存！正在应用新的设置..." if get_language() == "zh" 
                else "Settings saved! Applying new settings..."
            )
            
            # 强制刷新页面以应用新设置
            st.markdown(
                """
                <script>
                    setTimeout(function() {
                        window.parent.location.reload();
                    }, 1000);
                </script>
                """,
                unsafe_allow_html=True
            )
            st.stop()  # 停止当前页面的执行
        else:
            st.error(
                "保存设置失败！" if get_language() == "zh" 
                else "Failed to save settings!"
            )
    else:
        st.info(
            "设置未发生变化" if get_language() == "zh" 
            else "No changes in settings"
        )

# 添加清空配置按钮
if st.button("🗑️ " + ("清空配置" if get_language() == "zh" else "Clear Config")):
    if clear_config():
        st.success("配置已清空！" if get_language() == "zh" else "Config cleared!")
        st.session_state.clear()  # 清空 session_state
        st.experimental_rerun()  # 重新加载页面
    else:
        st.error("清空配置失败！" if get_language() == "zh" else "Failed to clear config!")

# 显示当前设置
st.divider()
st.subheader("🔍 " + ("当前设置" if get_language() == "zh" else "Current Settings"))

current_settings = {
    ("语言" if get_language() == "zh" else "Language"): 
        language_options[current_config['language']],
    ("主题" if get_language() == "zh" else "Theme"): 
        theme_options[current_config['theme']],
    "AI Model": current_config['ai_model'],
    "API Key": "****" + current_config['openai_api_key'][-4:] if current_config['openai_api_key'] else ("未设置" if get_language() == "zh" else "Not Set")
}

for key, value in current_settings.items():
    st.write(f"**{key}:** {value}") 