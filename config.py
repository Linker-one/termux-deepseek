import os
from typing import Dict, Any
from dotenv import load_dotenv
load_dotenv()

# 默认配置
DEFAULT_CONFIG: Dict[str, Any] = {
    "MODEL": "deepseek-ai/DeepSeek-V3",
    "API_URL": "https://api.siliconflow.cn/v1/chat/completions",
    "MAX_TOKENS": 8000,
    "TEMPERATURE": 0.7
}

def get_api_key() -> str:
    """从环境变量读取API Key"""
    key = os.getenv("SILICONFLOW_API_KEY")
    if not key:
        raise ValueError("未设置环境变量 SILICONFLOW_API_KEY")
    return key
