from chat_session import ChatSession
from cli_parser import parse_cli_args
from config import DEFAULT_CONFIG
from log_utils import setup_logging, log_interaction
from rich.markdown import Markdown
from rich.console import Console
from display_utils import MarkdownStreamRenderer

def main():
    # 初始化日志系统
    log_file = setup_logging()

    console = Console()
    
    # 解析命令行参数
    args = parse_cli_args()
    config = {k: v for k, v in args.items() if v is not None}
    
    # 初始化会话
    session = ChatSession(config)
    print(f"\n=== 模型:{config.get('model', DEFAULT_CONFIG['MODEL'])} ===")
    while True:
        try:
            print("\033[93m输入exit或quit退出\033[0m")
            # 用户输入
            user_input = input("\033[94m>>>用户: \033[0m").strip()
            # 记录用户输入
            log_interaction(log_file, f"**[用户]**:\n{user_input}\n\n")
            if user_input.lower() in ("exit", "quit"):
                break

            # 流式输出
            print(f"\033[92m<<<{config.get('model',DEFAULT_CONFIG['MODEL'])}:\033[0m",
                  end=" ", flush=True)
            full_response = ""
            renderer = MarkdownStreamRenderer()
            for chunk in session.stream_chat(user_input):
                full_response += chunk
                renderer.render(chunk)

            # 渲染剩余 buffer（最后一次输出）
            if renderer.buffer:
                renderer._process_buffer()
                
            #记录完整的响应
            log_interaction(log_file, f"**[{config.get('model',DEFAULT_CONFIG['MODEL'])}]**:" + 
                            f"\n{full_response}\n\n---\n\n")
            print("\n" + "=" * 40)

        except KeyboardInterrupt:
            print("\n\033[33m[中断当前回复]\033[0m")
            log_interaction(log_file, "[中断当前回复]\n\n")
            continue

    print(f"对话已保存到: {log_file}")

if __name__ == "__main__":
    main()
