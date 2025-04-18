import argparse
from typing import Dict, Any

def parse_cli_args() -> Dict[str, Any]:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="DeepSeek对话助手")
    parser.add_argument("--model", help="指定模型名称", default=None)
    parser.add_argument("--max-tokens", type=int, help="最大token数", default=None)
    parser.add_argument("--temperature", type=float, help="温度参数", default=None)
    return vars(parser.parse_args())
