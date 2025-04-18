#import re
import time
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).parent.resolve() / "logs"

'''def _sanitize_text(text: str) -> str:
    """清理文本中的无效Unicode字符"""
    if not text:
        return text
    # 移除无效的Unicode代理对字符 (U+D800到U+DFFF)
    return re.sub(r'[\ud800-\udfff]', '', text)'''

def setup_logging() -> Path:
    """初始化日志系统（增加编码错误处理）"""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        cleanup_old_logs()
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return LOG_DIR / f"{timestamp}.log"
    except Exception as e:
        print(f"❌ 日志系统初始化失败: {e}")
        raise

def cleanup_old_logs(days_to_keep: int = 7):
    """清理旧日志（增强错误处理）"""
    now = time.time()
    cutoff = now - (days_to_keep * 86400)
    
    for log_file in LOG_DIR.glob("*.log"):
        try:
            if log_file.stat().st_mtime < cutoff:
                log_file.unlink()
        except Exception as e:
            print(f"⚠️ 无法删除旧日志 {log_file.name}: {e}")

def log_interaction(log_file: Path, log_text: str):
    """安全记录交互日志"""

    # 清理输入文本
    #clean_text = _sanitize_text(log_text)
    try:
        with open(log_file, "a", encoding="utf-8", errors="replace") as f:
            #f.write(clean_text)
            f.write(log_text)
    except (IOError, BlockingIOError) as e:
        print(f"❌ 日志记录失败: {e}")
        # 尝试创建备份日志文件
        backup_log = LOG_DIR / "emergency.log"
        with open(backup_log, "a", encoding="utf-8", errors="replace") as f:
            f.write(f"[{datetime.now()}] 主日志写入失败: {e}\n")