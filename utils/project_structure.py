import os
import json
import subprocess
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass


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