import requests
import json
from typing import List, Dict, Any, Generator
import re
from config import DEFAULT_CONFIG, get_api_key


class ChatSession:
    """
    DeepSeek 对话会话管理类
    
    功能：
    - 维护对话历史记录
    - 处理流式API请求
    - 管理配置参数
    - 修复Unicode代理对字符导致的编码问题
    """

    def __init__(self, config_overrides: Dict[str, Any] = None):
        self.config = {**DEFAULT_CONFIG, **(config_overrides or {})}
        self.history: List[Dict[str, str]] = []
        self.api_key = get_api_key()

    def _sanitize_text(self, text: str) -> str:
        """清理文本中的无效Unicode代理对字符"""
        if not text:
            return text
        return re.sub(r'[\ud800-\udfff]', '', text)

    def stream_chat(self, user_input: str) -> Generator[str, None, None]:
        if not user_input.strip():
            raise ValueError("用户输入不能为空")
        
        clean_input = self._sanitize_text(user_input.strip())
        self.history.append({"role": "user", "content": clean_input})
        
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.config["MODEL"],
            "messages": self.history[-10:],  # 仅保留最近10条消息
            "stream": True,
            "temperature": self.config.get("TEMPERATURE", 0.7),
            "max_tokens": self.config.get("MAX_TOKENS", 2048)
        }

        full_response = ""
        try:
            with requests.post(
                self.config["API_URL"],
                json=payload,
                headers=headers,
                stream=True,
                timeout=(10, 30)  # 双重超时设置
            ) as response:
                response.raise_for_status()  # 自动处理4xx/5xx错误
                
                for line in response.iter_lines():
                    if not line or line == b"data: [DONE]":
                        continue
                    
                    try:
                        chunk = json.loads(line.decode("utf-8").lstrip("data: "))
                        if "choices" in chunk:
                            delta = self._sanitize_text(chunk["choices"][0]["delta"].get("content", ""))
                            full_response += delta
                            yield delta
                    except (json.JSONDecodeError, KeyError, UnicodeDecodeError) as e:
                        continue
        
        except requests.exceptions.Timeout:
            raise ConnectionError("请求超时，请检查网络连接")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"网络请求失败: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"处理响应时出错: {str(e)}")
        finally:
            if full_response:
                self.history.append({"role": "assistant", "content": full_response})
