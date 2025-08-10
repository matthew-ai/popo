import os
import datetime
from langchain_core.tools import tool

@tool(parse_docstring=True)
def read(file_path: str, offset: int = 1, limit: int = 2000) -> str:
    """
    Read a file from the local file system.

    Args:
        file_path: Absolute path of the file to read.
        offset: Line number to start reading from (starting at 1).
        limit: Number of lines to read.

    Returns:
        File content with line numbers (similar to cat -n format).

    Exceptions:
        ValueError: If file_path is not an absolute path.
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path is a directory.
        IOError: Other read errors.
    """
    if not os.path.isabs(file_path):
        raise ValueError(f"file_path 必须是绝对路径, 得到: {file_path}")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    if os.path.isdir(file_path):
        raise IsADirectoryError(f"路径是一个目录, 而不是文件: {file_path}")

    try:
        file_info = os.stat(file_path)
    except OSError as e:
        raise IOError(f"访问文件失败: {e}") from e

    # 设置默认值
    if offset <= 0:
        offset = 1
    if limit <= 0:
        limit = 2000

    lines = []
    try:
        # 使用 'with open' 来自动管理文件的打开和关闭
        # 使用 encoding='utf-8', errors='ignore' 来增强鲁棒性
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            current_line = 1

            # 跳过行直到达到偏移量
            while current_line < offset:
                if f.readline() == '':  # 文件结尾
                    break
                current_line += 1

            # 读取所需行数
            line_count = 0
            for line in f:
                if line_count >= limit:
                    break
                # rstrip() 用于删除行尾的换行符
                lines.append(f"{current_line:6d}\t{line.rstrip()}")
                current_line += 1
                line_count += 1
    except Exception as e:
        raise IOError(f"读取文件时出错: {e}") from e

    if not lines:
        return f"文件为空: {file_path}"

    result = "\n".join(lines)

    header = (
        f"File: {os.path.basename(file_path)} ({file_info.st_size} bytes, "
        f"modified: {datetime.datetime.fromtimestamp(file_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')})\n"
    )

    return header + "\n" + result