import os
import json
from pathlib import Path

def get_config_path():
    """获取配置文件路径"""
    config_dir = Path.home() / '.financial_chatbot'
    config_dir.mkdir(exist_ok=True)
    return config_dir / 'config.json'

def load_config():
    """加载配置"""
    config_path = get_config_path()
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return get_default_config()
    return get_default_config()

def save_config(config):
    """保存配置"""
    try:
        config_path = get_config_path()
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def get_default_config():
    """获取默认配置"""
    return {
        'language': 'zh',
        'ai_model': 'gpt-3.5-turbo',
        'openai_api_key': '',
        'theme': 'dark'
    }

def clear_config():
    """清空配置文件"""
    config_path = get_config_path()
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(get_default_config(), f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False 