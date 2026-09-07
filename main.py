import sys
from PyQt5.QtWidgets import QApplication
from auth import AuthWindow
from ui import PasswordManagerWindow
from database import initialize_database


# 移除了未使用的 check_credentials, create_user 导入，如果其他文件需要，它们自己会导入

def main():
    """
    主函数，负责程序的初始化和启动流程
    包括数据库初始化、Qt应用创建、登录验证和主窗口显示
    """
    # 初始化数据库
    initialize_database()

    # 创建Qt应用实例，传入系统参数
    app = QApplication(sys.argv)

    # 显示登录窗口并获取用户认证结果
    auth_window = AuthWindow()

    # 判断登录结果
    if auth_window.exec_() == AuthWindow.Accepted:
        # 登录成功，获取用户名（建议通过封装的方法获取，这里保留你的逻辑但提供优化建议）
        username = auth_window.username_input.text()

        # 显示主窗口
        main_window = PasswordManagerWindow(username)
        main_window.show()

        # 启动主事件循环，app.exec_() 会阻塞直到主窗口关闭，然后返回退出码给 sys.exit()
        sys.exit(app.exec_())
    else:
        # 登录失败或取消，无需调用 sys.exit(0)，直接返回即可终止主函数
        return


if __name__ == "__main__":
    main()
