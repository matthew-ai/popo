import os
import re
import fnmatch
from typing import List
from langchain_core.tools import tool

def _search_file_for_pattern(file_path: str, regex: re.Pattern) -> bool:
    """
    在单个文件中搜索给定的正则表达式模式。
    文件以二进制模式读取，以避免编码错误。

    参数:
    - file_path: 要搜索的文件的路径。
    - regex: 已编译的正则表达式对象 (用于字节串)。

    返回:
    - bool: 如果找到匹配项，则返回 True，否则返回 False。
    """
    try:
        # 以二进制模式('rb')打开文件，以避免在处理非UTF-8文件时出现解码错误。
        # 这种方法对于 grep 类的工具来说更健壮。
        with open(file_path, 'rb') as f:
            # 为了内存效率，分块读取，类似于原始Go代码的实现。
            chunk_size = 4096
            while chunk := f.read(chunk_size):
                if regex.search(chunk):
                    return True
    except (IOError, OSError):
        # 如果文件无法读取（例如权限问题），则跳过。
        return False
    return False

@tool(parse_docstring=True)
def grep(path: str, include: str, pattern: str) -> List[str]:
    """
    一个快速的内容搜索工具，可处理任何大小的代码库。
    它使用正则表达式搜索文件内容，并返回按修改时间排序的匹配文件路径。

    Args:
        path: 要搜索的目录。如果为空，则默认为当前工作目录。
        include: 要包含在搜索中的文件模式 (例如 "*.py", "*.{ts,tsx}")。
        pattern: 要在文件内容中搜索的正则表达式模式。

    Returns:
        List[str]: 包含匹配项的文件路径列表，按修改时间排序（最新的在前）。

    Raises:
        FileNotFoundError: 如果指定的目录不存在。
        NotADirectoryError: 如果指定的路径不是一个目录。
        re.error: 如果提供的正则表达式模式无效。
    """
    # 如果路径未指定，则使用当前工作目录
    if not path:
        path = os.getcwd()

    # 验证目录是否存在并获取其绝对路径
    if not os.path.isdir(path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"directory does not exist: {path}")
        raise NotADirectoryError(f"path is not a directory: {path}")

    abs_path = os.path.abspath(path)

    # 编译正则表达式模式。
    # 我们需要为字节串编译它，因为我们以二进制模式读取文件。
    try:
        # 将字符串模式编码为字节，以便在二进制内容上进行搜索
        regex = re.compile(pattern.encode('utf-8', errors='ignore'))
    except re.error as e:
        raise re.error(f"invalid regex pattern: {pattern}") from e

    matching_files_with_mtime = []

    # 遍历目录树
    for root, _, filenames in os.walk(abs_path):
        for filename in filenames:
            # 检查文件名是否匹配 include 模式
            if fnmatch.fnmatch(filename, include):
                full_path = os.path.join(root, filename)

                # 在文件中搜索模式
                if _search_file_for_pattern(full_path, regex):
                    try:
                        mod_time = os.path.getmtime(full_path)
                        matching_files_with_mtime.append((full_path, mod_time))
                    except OSError:
                        # 如果无法获取文件的修改时间，则忽略该文件
                        continue

    # 按修改时间对文件进行排序（最新的在前）
    matching_files_with_mtime.sort(key=lambda x: x[1], reverse=True)

    # 为更清晰的输出获取相对路径
    final_paths = [os.path.relpath(fpath, abs_path) for fpath, _ in matching_files_with_mtime]

    return final_paths