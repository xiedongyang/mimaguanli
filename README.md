# PyQt5 本地密码管理器
一个基于Python + PyQt5 + SQLite 的本地密码管理工具。
密码使用Fernet对称加密保存到SQLite数据库，用户登录密码使用PBKDF2‑SHA256加盐哈希存储。

> ⚠️重要提示：本项目为教学演示项目，内置硬编码演示加密密钥，**不适合直接用于生产环境**。
> 如果遗忘登录密码，数据库内保存的网站密码无法恢复。

## 功能特性
- 用户注册 / 用户登录
- 修改登录用户密码
- 密码分组管理（新增、重命名、删除分组）
- 密码条目管理：添加、编辑、删除、查看详情
- 双击密码列切换明文/掩码显示
- 所有密码本地加密存储在sqlite数据库文件
- 帮助弹窗提示，输入合法性校验
- Windows可打包为独立exe程序

## 项目文件说明
├─ main.py          # 程序入口，启动应用
├─ auth.py          # 登录注册窗口、密码哈希与校验
├─ ui.py            # 全部 Qt 界面、弹窗、密码加密解密
├─ database.py      # SQLite 数据库初始化与数据库操作函数
├─ build.py         # cx_Freeze 打包脚本（打包 exe 用，运行源码不需要）
└─ password_manager.db  # 运行后自动生成的 sqlite 数据库文件


### 文件依赖关系
1. `main.py` 导入 `auth`、`ui`、`database`，作为程序启动入口
2. `auth.py` 导入 `database`，处理用户注册登录密码哈希
3. `ui.py` 导入 `database`、`auth`，实现全部图形界面业务逻辑
4. `database.py` 负责全部SQLite数据库读写

## 环境依赖
Python >=3.8
需要安装依赖库：
pip install PyQt5 cryptography

打包 exe 额外需要 cx_Freeze
pip install cx_Freeze

运行源码
python main.py


首次运行会自动创建 `password_manager.db` 数据库文件。
首次使用勾选【注册新用户】创建账号。

## Windows 打包 exe

使用 cx_Freeze 打包：
python build.py build

打包完成输出在 `build` 文件夹内，生成 `PasswordManager.exe`。

> 
> 注意：打包后依然会在 exe 同级目录生成 `password_manager.db`。

## 使用说明

1. **注册账号**：勾选「注册新用户」，填写用户名密码，完成注册。
2. **登录**：取消勾选注册，输入用户名密码登录。
3. **分组管理**：左侧分组面板，可以新增、修改、删除分组。
4. **密码条目**：右侧添加 / 编辑密码，选择所属分组；站点名称不能为空。
5. **查看密码**：双击密码那一列，切换掩码 / 明文显示；双击其他列打开详情弹窗。
6. 修改登录密码：顶部菜单栏 → 编辑 → 修改用户信息。

## ⚠️安全限制与注意事项

1. 当前代码中 Fernet 加密密钥是硬编码写死在 `ui.py` 的 `DEMO_KEY`，**演示用途**。
   - 真实使用场景：每个用户应生成独立密钥，保存到安全位置，不能硬编码在代码。
2. 登录密码丢失**无法找回**，没有密码重置功能。
3. 数据库文件 `password_manager.db` 包含加密后的全部数据，请做好备份。
4. 本软件仅本地存储，没有云同步功能。

## 数据库表结构

- `users`：存储用户 id、用户名、pbkdf2 密码哈希
- `groups`：用户自定义密码分组
- `passwords`：加密后的密码记录，关联用户与分组，记录创建时间。

## 已知局限

- 无密码导出导入功能
- 无密码强度检测
- 加密密钥硬编码，不适合正式生产使用


## 补充建议
1. `build.py` 如果平时不打包，可以移动到单独文件夹 `pack/build.py`，保持源码目录干净。
2. `.gitignore` 建议增加，避免把数据库、打包产物提交：
password_manager.db
build/
dist/
**pycache**/
*.pyc