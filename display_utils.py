import re
from pygments import highlight
from pygments.lexers import get_lexer_by_name, PythonLexer #, guess_lexer
from pygments.formatters import TerminalFormatter
from termcolor import colored
from typing import Optional, List

terminal_formatter = TerminalFormatter()

class MarkdownStreamRenderer:
    def __init__(self):
        self.buffer = ""
        self.in_code_block = False
        self.code_block_lang: Optional[str] = None
        self.in_table = False
        self.table_rows: List[List[str]] = []
        self.table_header: Optional[List[str]] = None
        self.table_alignments: Optional[List[str]] = None

    def render(self, chunk: str) -> None:
        self.buffer += chunk
        self._process_buffer()

    def _process_buffer(self) -> None:
        while True:
            if not self.buffer:
                break

            # 1. 代码块检测（优先级最高）
            if not self.in_code_block and "```" in self.buffer:
                match = re.match(r'^(.*?)```(\w*)', self.buffer, re.DOTALL)
                if match:
                    self._render_non_code(match.group(1))
                    self.buffer = "\n" + "-" * 40 + "\n" + " " * 17 + "代码块\n" \
                        + "-" * 40 + self.buffer[len(match.group(0)):]
                    self.in_code_block = True
                    self.code_block_lang = match.group(2) or "text"
                    continue
            elif self.in_code_block and "```" in self.buffer:
                code_end_pos = self.buffer.find("```")
                code_content = self.buffer[:code_end_pos]
                self._render_code_block(code_content)
                self.buffer = "\n---" + self.buffer[code_end_pos + 3:]
                self.in_code_block = False
                continue

            # 2. 非代码块内容：表格、标题、列表等
            if not self.in_code_block:
                if self._detect_and_render_table():
                    continue

                line_end = self.buffer.find("\n")
                if line_end != -1:
                    line = self.buffer[:line_end]
                    self.buffer = self.buffer[line_end + 1:]
                    self._render_line(line + "\n")
                    continue
                else:
                    if len(self.buffer) > 200:
                        self._render_line(self.buffer)
                        self.buffer = ""
                    break
            else:
                break

    def _render_non_code(self, text: str) -> None:
        """渲染非代码内容（支持标题加粗、列表加粗/行内代码）"""
        if not text.strip():
            return

        # 检测分割线 ---
        if re.match(r'^---+$', text.strip()):
            print(colored("\n\n" + "-" * 40 + "\n", "grey"))
            return

        # 检测标题 ###**bold** or ####**bold**
        title_match = re.match(r'^(#{3,4})\s*(\*\*.*?\*\*)(.*)$', text.strip())
        if title_match:
            level = len(title_match.group(1))
            bold_part = title_match.group(2)[2:-2]  # 去掉 **
            rest_part = title_match.group(3)
            color = "blue" if level == 3 else "cyan"
            print(
                colored(bold_part, color, attrs=["bold"]) +
                colored(rest_part, color) + "\n"
            )
            return

        # 检测普通标题 ### text or #### text
        normal_title_match = re.match(r'^(#{3,4})\s*(.*)$', text.strip())
        if normal_title_match:
            level = len(normal_title_match.group(1))
            title_text = normal_title_match.group(2)
            color = "blue" if level == 3 else "cyan"
            print(colored(title_text, color, attrs=["bold"]) + "\n")
            return

        # 检测无序列表（支持列表内的加粗和行内代码）
        list_match = re.match(r'^\s*-\s+(.*)$', text.strip())
        if list_match:
            item_text = list_match.group(1)
            # 渲染列表项内的加粗 **text**
            item_text = re.sub(
                r'\*\*(.*?)\*\*',
                lambda m: colored(m.group(1), attrs=["bold"]),
                item_text
            )
            # 渲染列表项内的行内代码 `text`
            item_text = re.sub(
                r'`([^`]+)`',
                lambda m: colored(m.group(1), "light_grey", "on_dark_grey"),
                item_text
            )
            print(colored("• ", "dark_grey") + item_text)
            return

        # 渲染普通段落（加粗、斜体、行内代码）
        bold_italic_text = re.sub(r'\*\*(.*?)\*\*', lambda m: colored(m.group(1), attrs=["bold"]), text)
        bold_italic_text = re.sub(r'\*(.*?)\*', lambda m: colored(m.group(1), attrs=["italic"]), bold_italic_text)
        final_text = re.sub(
            r'`([^`]+)`',
            lambda m: colored(m.group(1), "light_grey", "on_dark_grey"),
            bold_italic_text
        )
        print(final_text, end="")

    def _render_code_block(self, code: str) -> None:
        if not code.strip():
            return
        lexer = (
            get_lexer_by_name(self.code_block_lang)
            if self.code_block_lang
            #else guess_lexer(code)
            else PythonLexer()
        )
        highlighted_code = highlight(code, lexer, terminal_formatter).rstrip()
        print(highlighted_code)

    def _detect_and_render_table(self) -> bool:
        """检测并渲染表格（逻辑不变）"""
        table_match = re.match(
            r'^(.*?)\|(.+?)\|\n\|([-|:\s]+)\|\n((?:\|.*\|\n)*)',
            self.buffer, re.DOTALL
        )
        if not table_match:
            return False

        prefix = table_match.group(1)
        headers = [h.strip() for h in table_match.group(2).split("|")]
        alignments = self._parse_table_alignments(table_match.group(3))
        rows = [
            [c.strip() for c in row.split("|")[1:-1]]
            for row in table_match.group(4).strip().split("\n")
            if row.strip()
        ]

        if prefix.strip():
            self._render_non_code(prefix)
        self._render_table(headers, alignments, rows)
        self.buffer = self.buffer[len(table_match.group(0)):]
        return True

    def _parse_table_alignments(self, align_line: str) -> List[str]:
        alignments = []
        for col in align_line.split("|"):
            col = col.strip()
            if col.startswith(":") and col.endswith(":"):
                alignments.append("center")
            elif col.startswith(":"):
                alignments.append("left")
            elif col.endswith(":"):
                alignments.append("right")
            else:
                alignments.append("left")
        return alignments

    def _render_table(self, headers: List[str], alignments: List[str], rows: List[List[str]]) -> None:
        col_widths = [
            max(len(headers[i]), *[len(row[i]) if i < len(row) else 0 for row in rows])
            for i in range(len(headers))
        ]

        border = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
        print(colored(border, "dark_grey"))

        header_row = "|"
        for h, w, align in zip(headers, col_widths, alignments):
            padded = (
                h.center(w) if align == "center"
                else h.ljust(w) if align == "left"
                else h.rjust(w)
            )
            header_row += f" {colored(padded, 'blue')} |"
        print(header_row)
        print(colored(border, "dark_grey"))

        for row in rows:
            row_str = "|"
            for cell, w, align in zip(row, col_widths, alignments):
                padded = (
                    cell.center(w) if align == "center"
                    else cell.ljust(w) if align == "left"
                    else cell.rjust(w)
                )
                row_str += f" {colored(padded, 'light_grey')} |"
            print(row_str)

        print(colored(border, "dark_grey") + "\n")

    def _render_line(self, line: str) -> None:
        if line.strip() == "---":
            print(colored("-" * 40, "grey") + "\n")
            return
        self._render_non_code(line)