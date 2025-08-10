import os
import glob  as py_glob
from typing import List
from langchain_core.tools import tool

@tool(parse_docstring=True)
def glob(path: str, pattern: str) -> List[str]:
    """
    Glob 是一个快速的文件模式匹配工具，适用于任何规模的代码库。
    它支持像 "**/*.js" 或 "src/**/*.ts" 这样的 glob 模式，并按字典顺序返回匹配的文件路径。

    Args:
      path (str): 要搜索的目录。如果未指定，将使用当前工作目录。
      pattern (str): 用于匹配文件的 glob 模式。

    Returns:
      list[str]: 按字典顺序排列的匹配文件路径数组。

    Raises:
      FileNotFoundError: 如果指定的路径不存在或不是一个目录。
    """
    # 如果未指定路径，则使用当前工作目录
    search_path = path if path else os.getcwd()

    # 验证目录是否存在
    if not os.path.isdir(search_path):
        raise FileNotFoundError(f"目录不存在: {search_path}")

    # 构造完整的搜索模式
    full_pattern = os.path.join(search_path, pattern)

    # 使用 glob 并设置 recursive=True 来处理 "**"
    matches = py_glob.glob(full_pattern, recursive=True)

    # 过滤掉目录并获取相对路径
    files = []
    for match in matches:
        if os.path.isfile(match):
            # 转换为相对于 search_path 的路径
            rel_path = os.path.relpath(match, search_path)
            files.append(rel_path)

    # 按字典顺序排序
    files.sort()

    return files