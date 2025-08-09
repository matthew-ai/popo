import os
import json
import subprocess
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from typing import Any


@dataclass
class RepoInfo:
    """项目仓库信息结构体"""
    currentDirectory: str          # 当前工作目录
    rootPath: str                  # 仓库根目录
    repoURL: str                   # 仓库远程URL（优先取origin）
    repoPath: str                  # 仓库根目录绝对路径
    Branch: str                    # 当前分支
    status: str                    # git status信息
    recentCommit: List[str]        # 最近commit信息列表（哈希、作者、日期、信息等）
    directoryStructure: str        # 目录结构（JSON字符串）
    hasReadme: bool                # 是否有README文件
    hasMakefile: bool              # 是否有Makefile
    totalFiles: int                # 总文件数
    totalDirectories: int          # 总目录数（不含.git等忽略目录）

def get_project_structure() -> Optional[RepoInfo]:
    """获取项目仓库信息并返回RepoInfo实例"""
    try:
        # 1. 基础路径信息
        current_dir = os.getcwd()
        root_path = subprocess.check_output(
            ['git', 'rev-parse', '--show-toplevel'],
            stderr=subprocess.STDOUT,
            text=True
        ).strip()



        # 2. 远程仓库URL（优先取origin）
        remote_info = subprocess.check_output(
            ['git', 'remote', '-v'],
            stderr=subprocess.STDOUT,
            text=True
        ).strip()
        repo_url = ""
        for line in remote_info.split('\n'):
            if line.startswith('origin') and 'fetch' in line:
                repo_url = line.split()[1]
                break

        # 3. 分支信息
        branch_output = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            stderr=subprocess.STDOUT,
            text=True
        ).strip()
        current_branch = branch_output

        # 4. 状态信息
        status_info = subprocess.check_output(
            ['git', 'status'],
            stderr=subprocess.STDOUT,
            text=True
        ).strip()

        # 5. 最近commit信息
        commit_output = subprocess.check_output(
            ['git', 'log', '-1', '--pretty=format:%H%n%an%n%ae%n%ad%n%s'],
            stderr=subprocess.STDOUT,
            text=True
        ).strip()
        recent_commit = commit_output.split('\n')

        # 6. 目录结构及统计（同时计算文件和目录数量）
        ignore_dirs = {'.git', '__pycache__', '.idea', '.vscode', 'node_modules'}
        total_files = 0
        total_dirs = 0

        def build_markdown_tree(path: Path, prefix: str = "", is_last: bool = True) -> str:
            """递归构建Markdown树形结构字符串"""
            nonlocal total_files, total_dirs

            # 忽略指定目录
            if path.name in ignore_dirs:
                return ""

            # 统计目录
            if path.is_dir():
                total_dirs += 1
                item_str = f"{path.name}/"
            else:
                total_files += 1
                item_str = path.name

            # 确定当前行的前缀符号
            if prefix == "":  # 根节点
                line = f"- {item_str}\n"
            else:
                connector = "└── " if is_last else "├── "
                line = f"{prefix}{connector}{item_str}\n"

            # 如果是目录，递归处理子项
            if path.is_dir() and path.name not in ignore_dirs:
                children = []
                for item in path.iterdir():
                    if item.name not in ignore_dirs:
                        children.append(item)

                # 处理子项的前缀
                if is_last:
                    new_prefix = f"{prefix}    "
                else:
                    new_prefix = f"{prefix}│   "

                # 递归添加子项
                for i, child in enumerate(children):
                    is_last_child = (i == len(children) - 1)
                    line += build_markdown_tree(child, new_prefix, is_last_child)

            return line

        # 从根目录开始构建树形结构
        root_path_obj = Path(root_path)
        dir_structure = build_markdown_tree(root_path_obj)

        # 7. 检查是否有README和Makefile
        has_readme = any(
            root_path_obj.joinpath(f).exists()
            for f in ['README', 'README.md', 'readme', 'readme.md']
        )
        has_makefile = root_path_obj.joinpath('Makefile').exists() or root_path_obj.joinpath('makefile').exists()

        # 构建并返回结构体
        return RepoInfo(
            currentDirectory=current_dir,
            rootPath=root_path,
            repoURL=repo_url,
            repoPath=root_path,
            Branch=current_branch,
            status=status_info,
            recentCommit=recent_commit,
            directoryStructure=dir_structure,
            hasReadme=has_readme,
            hasMakefile=has_makefile,
            totalFiles=total_files,
            totalDirectories=total_dirs
        )

    except subprocess.CalledProcessError as e:
        print(f"Git命令执行错误: {e.output}")
        return None
    except Exception as e:
        print(f"发生错误: {str(e)}")
        return None


def class_to_xml(obj: Any, root_tag: str = None) -> str:
    """
    将Python类实例转换为XML格式字符串

    参数:
        obj: 任意类实例
        root_tag: 根节点标签名（默认使用类名）
    返回:
        格式化后的XML字符串
    """
    # 根节点标签默认使用类名（首字母小写处理）
    if root_tag is None:
        root_tag = obj.__class__.__name__.lower()
    root = Element(root_tag)

    # 递归处理属性的函数
    def build_xml(element: Element, name: str, value: Any):
        # 处理基本类型（字符串、数字、布尔值、None）
        if isinstance(value, (str, int, float, bool, type(None))):
            elem = SubElement(element, name)
            elem.text = str(value).lower() if isinstance(value, bool) else str(value)
            return

        # 处理列表/元组等可迭代对象
        if isinstance(value, (list, tuple)):
            list_elem = SubElement(element, name)
            for item in value:
                # 列表项统一用<item>标签，递归处理内容
                build_xml(list_elem, "item", item)
            return

        # 处理嵌套的类实例（非内置类型）
        if hasattr(value, '__dict__'):  # 检查是否为自定义类实例
            obj_elem = SubElement(element, name)
            # 遍历实例的属性字典（排除私有属性）
            for attr_name, attr_value in value.__dict__.items():
                if not attr_name.startswith('__'):  # 跳过私有属性
                    # 属性名作为标签名（替换特殊字符）
                    safe_name = attr_name.replace("_", "-").lower()
                    build_xml(obj_elem, safe_name, attr_value)
            return

        # 其他类型（如字典）
        if isinstance(value, dict):
            dict_elem = SubElement(element, name)
            for key, val in value.items():
                safe_key = key.replace("_", "-").lower()
                build_xml(dict_elem, safe_key, val)
            return

    # 遍历当前类实例的所有属性（排除私有属性）
    for attr_name, attr_value in obj.__dict__.items():
        if not attr_name.startswith('__'):  # 跳过__module__、__doc__等内置属性
            safe_attr_name = attr_name.replace("_", "-").lower()
            build_xml(root, safe_attr_name, attr_value)

    # 格式化XML（增加缩进和换行）
    rough_xml = tostring(root, 'utf-8')
    parsed_xml = minidom.parseString(rough_xml)
    return parsed_xml.toprettyxml(indent="  ")


def get_project_structure_xml() -> Optional[str]:
    """获取项目仓库信息并返回 XML 字符串"""
    repo_info = get_project_structure()
    if repo_info:
        return class_to_xml(repo_info)
    return None

if __name__ == "__main__":
    repo_info = get_project_structure()
    if repo_info:
        print("项目仓库信息:")
        print(f"当前目录: {repo_info.currentDirectory}")
        print(f"仓库根目录: {repo_info.rootPath}")
        print(f"仓库URL: {repo_info.repoURL}")
        print(f"仓库路径: {repo_info.repoPath}")
        print(f"当前分支: {repo_info.Branch}")
        print(f"状态: {repo_info.status}")
        print(f"最近提交: {repo_info.recentCommit}")
        print(f"目录结构: {repo_info.directoryStructure}")
        print(f"是否有README: {repo_info.hasReadme}")
        print(f"是否有Makefile: {repo_info.hasMakefile}")
        print(f"总文件数: {repo_info.totalFiles}")
        print(f"总目录数: {repo_info.totalDirectories}")

    print(get_project_structure_xml())