from cx_Freeze import setup, Executable
import sys

# 基础配置
base = None
if sys.platform == "win32":
    base = "Win32GUI"  # 隐藏控制台窗口

# 包含的文件
include_files = []
includes = []
excludes = []
packages = ["PyQt5", "sqlite3"]

# 构建选项
build_options = {
    "includes": includes,
    "excludes": excludes,
    "packages": packages,
    "include_files": include_files,
    "optimize": 2
}

# 可执行文件配置
executables = [
    Executable(
        "main.py",
        base=base,
        target_name="PasswordManager.exe",
        icon=None  # 可以添加图标文件路径
    )
]

# 设置信息
setup(
    name="Password Manager",
    version="1.0",
    description="A secure password management application",
    options={"build_exe": build_options},
    executables=executables
)