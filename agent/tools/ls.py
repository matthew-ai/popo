import os
import stat
import fnmatch
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional
from langchain_core.tools import tool

@dataclass
class FileInfo:
    """用于封装文件或目录信息的类。"""
    name: str
    path: str
    size: int
    is_dir: bool
    mod_time: str
    mode: str
    full_path: str


def should_ignore(name: str, full_path: str, ignore_patterns: Optional[List[str]]) -> bool:
    """
    根据 glob 模式检查是否应忽略某个文件或目录。
    此函数模仿了原始 Go 实现的行为，包括其对 '/*' 和 '**' 的特定处理方式。

    参数:
    - name: 文件或目录的名称。
    - full_path: 文件或目录的绝对路径。
    - ignore_patterns: 用于忽略的 glob 模式列表。

    返回:
    - bool: 如果条目应被忽略，则返回 True，否则返回 False。
    """
    if not ignore_patterns:
        return False

    for pattern in ignore_patterns:
        # 检查是否匹配文件名
        if fnmatch.fnmatch(name, pattern):
            return True

        # 检查是否匹配完整路径
        if fnmatch.fnmatch(full_path, pattern):
            return True

        # 模仿 Go 代码的逻辑，处理以 '/*' 结尾的目录模式
        if pattern.endswith("/*"):
            dir_pattern = pattern[:-2]
            if full_path.startswith(dir_pattern):
                return True

        # 模仿 Go 代码的逻辑，通过简化来处理 '**' 模式
        if "**" in pattern:
            simple_pattern = pattern.replace("**", "*")
            if fnmatch.fnmatch(full_path, simple_pattern):
                return True

    return False


@tool(parse_docstring=True)
def ls(path: str, ignore: Optional[List[str]] = None) -> List[FileInfo]:
    """
    列出给定路径中的文件和目录。路径参数必须是绝对路径。
    您可以选择性地提供一个 glob 模式列表以忽略某些条目。

    Args:
      path: 要列出内容的目录的绝对路径。
      ignore: (可选) 用于忽略的 glob 模式列表。

    Returns:
      List[FileInfo]: 一个包含文件/目录信息对象的列表。

    Raises:
      ValueError: 如果路径不是绝对路径。
      FileNotFoundError: 如果路径不存在。
      NotADirectoryError: 如果路径不是一个目录。
      IOError: 如果读取目录时发生错误。
    """
    # 验证路径是否为绝对路径
    if not os.path.isabs(path):
        raise ValueError(f"path must be an absolute path, got: {path}")

    # 验证目录是否存在且确实是一个目录
    if not os.path.isdir(path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"failed to access path: {path}")
        raise NotADirectoryError(f"path is not a directory: {path}")

    file_infos = []

    # 使用 os.scandir 以获得更好的性能
    try:
        with os.scandir(path) as entries:
            for entry in entries:
                full_path = os.path.join(path, entry.name)

                # 检查此条目是否应被忽略
                if should_ignore(entry.name, full_path, ignore):
                    continue

                try:
                    info = entry.stat()

                    # 创建 FileInfo 对象
                    file_info = FileInfo(
                        name=entry.name,
                        path=full_path,
                        size=info.st_size,
                        is_dir=entry.is_dir(),
                        mod_time=datetime.fromtimestamp(info.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                        mode=stat.filemode(info.st_mode),
                        full_path=full_path,
                    )
                    file_infos.append(file_info)
                except OSError:
                    # 如果无法获取条目信息，则跳过，与 Go 的行为一致
                    continue
    except OSError as e:
        raise IOError(f"failed to read directory: {e}") from e

    # 按名称排序 (目录优先，然后是文件，不区分大小写)
    file_infos.sort(key=lambda f: (not f.is_dir, f.name.lower()))

    return file_infos

