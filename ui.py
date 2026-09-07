from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QListWidget, QTreeWidget, QPushButton, QStatusBar,
    QMessageBox, QInputDialog, QTreeWidgetItem, QFileDialog,
    QLabel, QDialog, QTextEdit, QAction, QListWidgetItem, QLineEdit,
    QToolTip, QComboBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont
from cryptography.fernet import Fernet
import base64
from typing import Optional
import auth
from datetime import datetime, timedelta

# 导入数据库函数，并加上 db_ 前缀以避免命名冲突
from database import (
    get_user_id as db_get_user_id,
    get_groups as db_get_groups,
    add_group as db_add_group,
    add_password as db_add_password,
    get_passwords as db_get_passwords,
    update_password as db_update_password,
    delete_password as db_delete_password,
    get_group_id as db_get_group_id,
    get_password_details as db_get_password_details,
    delete_selected_group as db_delete_selected_group,
    update_user_password as db_update_user_password,
    update_group_name
)

QToolTip.setFont(QFont("SimSun", 10))

# ========= 加密工具类 =========
# 演示密钥，生产环境不能硬编码！真实项目密钥应当每个用户独立保存
DEMO_KEY = b'abcdefghijklmnopqrstuvwxyz1234567890ABCDEF='
FIX_KEY = base64.urlsafe_b64encode(DEMO_KEY[:32])
fernet = Fernet(FIX_KEY)


class PasswordManagerWindow(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.user_id = db_get_user_id(username)
        if not self.user_id:
            print(f"错误：找不到用户 {username} 的 ID")
            return
        self.current_group = "所有密码"
        self.init_ui()
        self.password_data = {}  # key: password_id, value dict

    def encrypt_password(self, plain_text: str) -> Optional[str]:
        """加密明文密码，返回字符串，异常返回None"""
        try:
            return fernet.encrypt(plain_text.encode("utf-8")).decode("utf-8")
        except Exception as e:
            print("加密异常", e)
            return None

    def decrypt_password(self, cipher_text: str) -> Optional[str]:
        """解密密文，失败返回None"""
        try:
            return fernet.decrypt(cipher_text.encode("utf-8")).decode("utf-8")
        except Exception as e:
            print("解密失败", e)
            return None

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("密码管理器")
        self.resize(1500, 620)
        self.create_menu_bar()

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)

        # 左侧分组面板
        self.group_panel = QGroupBox("分组")
        group_layout = QVBoxLayout()
        self.group_list = QListWidget()
        self.group_list.itemClicked.connect(self.on_group_selected)
        group_layout.addWidget(self.group_list)

        group_btn_layout = QHBoxLayout()
        self.add_group_btn = QPushButton("添加")
        self.add_group_btn.clicked.connect(self.on_add_group)
        group_btn_layout.addWidget(self.add_group_btn)
        self.edit_group_btn = QPushButton("修改")
        self.edit_group_btn.clicked.connect(self.on_edit_group)
        group_btn_layout.addWidget(self.edit_group_btn)
        self.delete_group_btn = QPushButton("删除")
        self.delete_group_btn.clicked.connect(self.on_delete_group)
        group_btn_layout.addWidget(self.delete_group_btn)
        group_layout.addLayout(group_btn_layout)
        self.group_panel.setLayout(group_layout)

        # 右侧密码面板
        self.password_panel = QGroupBox("密码条目")
        password_layout = QVBoxLayout()
        self.password_tree = QTreeWidget()
        self.password_tree.setHeaderLabels(["标题", "用户名", "密码", "网站", "备注", "创建时间"])
        self.password_tree.itemDoubleClicked.connect(self.tree_item_double_click)
        password_layout.addWidget(self.password_tree)

        password_btn_layout = QHBoxLayout()
        self.add_password_btn = QPushButton("添加")
        self.add_password_btn.clicked.connect(self.on_add_password)
        password_btn_layout.addWidget(self.add_password_btn)
        self.edit_password_btn = QPushButton("编辑")
        self.edit_password_btn.clicked.connect(self.on_edit_password)
        password_btn_layout.addWidget(self.edit_password_btn)
        self.delete_password_btn = QPushButton("删除")
        self.delete_password_btn.clicked.connect(self.on_delete_password)
        password_btn_layout.addWidget(self.delete_password_btn)
        password_layout.addLayout(password_btn_layout)
        self.password_panel.setLayout(password_layout)

        main_layout.addWidget(self.group_panel, 1)
        main_layout.addWidget(self.password_panel, 3)

        self.load_groups()
        self.load_passwords()

    # ================= 分组相关方法 =================
    def load_groups(self):
        self.group_list.clear()
        all_item = QListWidgetItem("所有密码")
        all_item.setData(Qt.UserRole, None)
        self.group_list.addItem(all_item)
        groups = db_get_groups(self.user_id)
        for group_id, group_name in groups:
            item = QListWidgetItem(group_name)
            item.setData(Qt.UserRole, group_id)
            self.group_list.addItem(item)
        self.group_list.setCurrentRow(0)

    def on_group_selected(self, item):
        self.current_group = item.text()
        group_id = item.data(Qt.UserRole)
        self.load_passwords(group_id)

    def on_add_group(self):
        group_name, ok = QInputDialog.getText(self, "新建分组", "请输入分组名称:")
        if not ok or not group_name.strip():
            QMessageBox.warning(self, "提示", "分组名称不能为空!")
            return
        group_name = group_name.strip()
        existing_groups = db_get_groups(self.user_id)
        if group_name in [g[1] for g in existing_groups]:
            QMessageBox.warning(self, "错误", f"分组 '{group_name}' 已存在!")
            return
        print(f"尝试添加分组: {group_name}, 用户ID: {self.user_id}")
        if db_add_group(self.user_id, group_name):
            print("添加分组成功!")
            self.load_groups()
            items = self.group_list.findItems(group_name, Qt.MatchExactly)
            if items:
                self.group_list.setCurrentItem(items[0])
                self.on_group_selected(items[0])
            QMessageBox.information(self, "成功", f"分组 '{group_name}' 添加成功!")
        else:
            print("添加分组失败!")
            QMessageBox.warning(self, "错误", "添加分组失败，请重试!")

    def on_delete_group(self):
        current_item = self.group_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "提示", "请先选择一个分组!")
            return
        current_text = current_item.text()
        current_id = current_item.data(Qt.UserRole)
        if not current_id or current_text in ["所有密码", "所有分组"]:
            QMessageBox.warning(self, "提示", "无法删除系统默认分组!")
            return
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除分组 '{current_text}' 吗?\n该分组下的密码将移至'未分组'状态。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if db_delete_selected_group(current_id):
                if self.current_group == current_text:
                    self.current_group = "所有密码"
                    self.group_list.setCurrentRow(0)
                self.load_groups()
                self.load_passwords()
                QMessageBox.information(self, "成功", "分组已删除!")
            else:
                QMessageBox.warning(self, "错误", "删除分组失败!")

    def on_edit_group(self):
        """修改分组名称"""
        current_item = self.group_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "提示", "请先选择一个分组！")
            return

        group_text = current_item.text()
        group_id = current_item.data(Qt.UserRole)

        # 虚拟分组【所有密码】禁止修改，group_id为None
        if group_id is None:
            QMessageBox.warning(self, "提示", "虚拟分组「所有密码」不能修改！")
            return

        new_name, ok = QInputDialog.getText(self, "修改分组名称", "请输入新分组名称:", text=group_text)
        if not ok or not new_name.strip():
            return
        new_name = new_name.strip()

        # 获取当前用户全部分组，判断是否重名
        all_groups = db_get_groups(self.user_id)
        exist_names = [g[1] for g in all_groups]
        # 如果新名字和别的分组重名（排除自己本身）
        if new_name in exist_names and new_name != group_text:
            QMessageBox.warning(self, "错误", f"分组「{new_name}」已经存在！")
            return

        if update_group_name(group_id, new_name):
            QMessageBox.information(self, "成功", f"分组已修改为：{new_name}")
            self.load_groups()
        else:
            QMessageBox.warning(self, "失败", "修改分组名称失败！")

    # ================= 密码相关方法 =================
    def load_passwords(self, group_id=None):
        self.password_tree.clear()
        self.password_data = {}
        data_list = db_get_passwords(self.user_id, group_id)
        for row_data in data_list:
            p_id, site_name, site_url, username, enc_pwd, notes, created_at = row_data
            item = QTreeWidgetItem(self.password_tree)
            item.setText(0, site_name)
            item.setText(1, username)
            item.setText(2, '*' * 8)
            item.setText(3, site_url)
            item.setText(4, notes)
            item.setText(5, str(created_at))  # 原样输出，不做时间加减
            item.setData(0, Qt.UserRole, p_id)

            self.password_data[p_id] = {
                'item': item,
                'enc_pwd': enc_pwd,
                'is_visible': False
            }

    def tree_item_double_click(self, item, column):
        """统一双击事件：密码列双击切换明文密文；其他列双击弹出详情"""
        p_id = item.data(0, Qt.UserRole)
        if p_id is None:
            return
        if column == 2:
            self.toggle_password_visibility(item, p_id)
        else:
            self.on_show_password_details(item, column)

    def toggle_password_visibility(self, item, p_id):
        data = self.password_data[p_id]
        enc_pwd = data['enc_pwd']
        is_visible = data['is_visible']
        try:
            if is_visible:
                item.setText(2, '*' * 8)
                data['is_visible'] = False
            else:
                decrypted_pwd = self.decrypt_password(enc_pwd)
                if decrypted_pwd:
                    item.setText(2, decrypted_pwd)
                    data['is_visible'] = True
                else:
                    item.setText(2, "解密失败")
                    data['is_visible'] = False
        except Exception as e:
            item.setText(2, "显示错误")
            print(f"密码显示错误: {str(e)}")
        self.password_data[p_id] = data

    def on_add_password(self):
        dialog = PasswordEntryDialog(self)
        dialog.setWindowTitle("添加密码")
        # ✅ exec_之前填充分组下拉
        dialog.fill_groups(self.user_id, None)
        ret = dialog.exec_()
        if ret == PasswordEntryDialog.Accepted:
            try:
                site_name = dialog.title_input.text().strip()
                username = dialog.username_input.text().strip()
                plain_pwd = dialog.password_input.text()
                site_url = dialog.website_input.text().strip()
                notes = dialog.notes_input.toPlainText()
                group_id = dialog.get_selected_group_id()

                encrypted = self.encrypt_password(plain_pwd)
                if encrypted is None:
                    QMessageBox.warning(self, "错误", "密码加密失败！")
                    return
                ok = db_add_password(self.user_id, group_id, site_name, site_url, username, encrypted, notes)
                if ok:
                    self.load_passwords(group_id)
                else:
                    QMessageBox.warning(self, "错误", "添加密码失败!")
            except Exception as e:
                print("添加密码异常", e)
                QMessageBox.critical(self, "异常", f"发生异常：{str(e)}")

    def on_edit_password(self):
        selected_items = self.password_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "错误", "请先选择一个密码条目!")
            return
        item = selected_items[0]
        password_id = item.data(0, Qt.UserRole)
        if password_id is None:
            QMessageBox.warning(self, "错误", "无法获取密码ID！")
            return
        password_data = db_get_password_details(password_id)
        if not password_data:
            QMessageBox.warning(self, "错误", "读取密码详情失败")
            return

        dialog = PasswordEntryDialog(self)
        dialog.setWindowTitle("编辑密码")
        # ✅解包： p_id, g_id, site_name, site_url, username, enc_pwd, notes
        _, current_gid, site_name, site_url, username, enc_pwd, notes = password_data
        # ✅exec_之前填充分组，回显当前分组
        dialog.fill_groups(self.user_id, current_gid)

        dialog.title_input.setText(site_name)
        dialog.website_input.setText(site_url)
        dialog.username_input.setText(username)
        dialog.password_input.setText(self.decrypt_password(enc_pwd))
        dialog.notes_input.setPlainText(notes)

        if dialog.exec_() == PasswordEntryDialog.Accepted:
            try:
                site_name = dialog.title_input.text().strip()
                site_url = dialog.website_input.text().strip()
                username = dialog.username_input.text().strip()
                plain_pwd = dialog.password_input.text()
                notes = dialog.notes_input.toPlainText()
                new_group_id = dialog.get_selected_group_id()

                encrypted_new = self.encrypt_password(plain_pwd)
                if encrypted_new is None:
                    QMessageBox.warning(self, "错误", "加密失败")
                    return
                if db_update_password(password_id, new_group_id, site_name, site_url, username, encrypted_new, notes):
                    self.load_passwords(new_group_id)
                else:
                    QMessageBox.warning(self, "错误", "更新密码失败!")
            except Exception as e:
                print("编辑密码异常", e)
                QMessageBox.critical(self, "异常", str(e))

    def on_delete_password(self):
        selected_items = self.password_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "提示", "请先选择一个密码条目!")
            return
        item = selected_items[0]
        password_id = item.data(0, Qt.UserRole)
        title = item.text(0)
        if not password_id:
            QMessageBox.warning(self, "错误", "无法获取该条目的ID，删除失败!")
            return
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除密码条目 '{title}' 吗?\n此操作无法撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if db_delete_password(password_id):
                self.load_passwords()
                QMessageBox.information(self, "成功", "删除成功!")
            else:
                QMessageBox.warning(self, "错误", "删除密码失败!")

    def on_modify_user_info(self):
        """打开修改用户信息弹窗"""
        dialog = ModifyUserInfoDialog(self, self.user_id)
        dialog.exec_()

    def on_show_password_details(self, item, column):
        password_id = item.data(0, Qt.UserRole)
        if not password_id:
            return
        details = db_get_password_details(password_id)
        if details:
            _, _, site_name, site_url, username, enc_pwd, notes = details
            dec_pwd = self.decrypt_password(enc_pwd) or "解密失败"
            dlg = PasswordDetailDialog(self, site_name, site_url, username, dec_pwd, notes)
            dlg.exec_()

    # ================= 菜单和工具栏方法 =================
    def create_menu_bar(self):
        menubar = self.menuBar()
        # 文件菜单
        file_menu = menubar.addMenu('文件')
        exit_action = QAction(QIcon(), '退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 编辑菜单：修改用户信息
        edit_menu = menubar.addMenu('编辑')
        modify_user_action = QAction(QIcon(), '修改用户信息', self)
        modify_user_action.setShortcut('Ctrl+U')
        modify_user_action.triggered.connect(self.on_modify_user_info)
        edit_menu.addAction(modify_user_action)

        # 帮助菜单
        help_menu = menubar.addMenu('帮助')
        about_action = QAction(QIcon(), '关于', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)



    def show_about(self):
        QMessageBox.about(self, "关于",
                          "密码管理器 v1.0\n\n"
                          "一个简单的密码管理工具\n\n"
                          "© 2026 All Rights Reserved")


class PasswordDetailDialog(QDialog):
    """密码详情弹窗，内置自定义帮助按钮，移除系统问号"""
    def __init__(self, parent, site_name, site_url, username, dec_pwd, notes):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("密码详情")
        self.resize(420, 260)
        layout = QVBoxLayout()
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("<b>密码详情</b>"))
        top_layout.addStretch(1)
        help_btn = QPushButton("?")
        help_btn.setFixedSize(24, 24)
        help_btn.setToolTip("点击查看密码详情窗口帮助信息")
        help_btn.clicked.connect(self.show_help)
        top_layout.addWidget(help_btn)
        layout.addLayout(top_layout)

        layout.addWidget(QLabel(f"站点名称: {site_name}"))
        layout.addWidget(QLabel(f"网站地址: {site_url}"))
        layout.addWidget(QLabel(f"用户名: {username}"))
        layout.addWidget(QLabel(f"密码: {dec_pwd}"))
        layout.addWidget(QLabel(f"备注: {notes}"))

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        self.setLayout(layout)

    def show_help(self):
        help_text = """【密码详情帮助】
1. 此窗口用于查看单条密码完整信息
2. 密码字段为明文展示
3. 如果要修改记录，请关闭本窗口，点击主窗口编辑按钮
4. 需要复制密码，直接选中文字复制即可
"""
        QMessageBox.information(self, "帮助", help_text)





# 密码输入对话框类（添加/编辑密码）
class PasswordEntryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("添加密码")
        self.setModal(True)
        layout = QVBoxLayout()

        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("<b>添加密码</b>"))
        top_layout.addStretch(1)
        help_btn = QPushButton("?")
        help_btn.setFixedSize(24, 24)
        help_btn.setToolTip("点击查看添加/编辑密码帮助")
        help_btn.clicked.connect(self.show_help)
        top_layout.addWidget(help_btn)
        layout.addLayout(top_layout)

        layout.addWidget(QLabel("站点名称:"))
        self.title_input = QLineEdit()
        layout.addWidget(self.title_input)

        layout.addWidget(QLabel("所属分组:"))
        self.group_combo = QComboBox()
        layout.addWidget(self.group_combo)

        layout.addWidget(QLabel("网站地址:"))
        self.website_input = QLineEdit()
        layout.addWidget(self.website_input)

        layout.addWidget(QLabel("用户名:"))
        self.username_input = QLineEdit()
        layout.addWidget(self.username_input)

        layout.addWidget(QLabel("密码:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        layout.addWidget(QLabel("备注:"))
        self.notes_input = QTextEdit()
        layout.addWidget(self.notes_input)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def fill_groups(self, user_id, current_group_id=None):
        self.group_combo.clear()
        self.group_combo.addItem("未分组", None)
        groups = db_get_groups(user_id)
        for g_id, g_name in groups:
            self.group_combo.addItem(g_name, g_id)
        if current_group_id is None:
            self.group_combo.setCurrentIndex(0)
        else:
            for idx in range(self.group_combo.count()):
                stored_id = self.group_combo.itemData(idx)
                if stored_id == current_group_id:
                    self.group_combo.setCurrentIndex(idx)
                    break

    def get_selected_group_id(self):
        return self.group_combo.currentData()

    def accept(self):
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "输入校验", "站点名称不能为空！")
            return
        super().accept()

    def show_help(self):
        txt = """【添加/编辑密码帮助】
1. 站点名称不能为空
2. 所属分组可以修改，用于归类密码条目
3. 网站地址填写完整URL，例如 https://www.baidu.com
4. 保存后密码自动加密存储在本地数据库
"""
        QMessageBox.information(self, "帮助", txt)


# 修改用户信息弹窗
class ModifyUserInfoDialog(QDialog):
    def __init__(self, parent=None, user_id: int = 0):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("修改用户密码")
        self.setModal(True)
        self.resize(320, 260)
        layout = QVBoxLayout()

        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("<b>修改用户密码</b>"))
        top_layout.addStretch(1)
        help_btn = QPushButton("?")
        help_btn.setFixedSize(24, 24)
        help_btn.setToolTip("点击查看修改用户密码帮助")
        help_btn.clicked.connect(self.show_help)
        top_layout.addWidget(help_btn)
        layout.addLayout(top_layout)

        layout.addWidget(QLabel("旧密码:"))
        self.old_pwd = QLineEdit()
        self.old_pwd.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.old_pwd)

        layout.addWidget(QLabel("新密码:"))
        self.new_pwd = QLineEdit()
        self.new_pwd.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.new_pwd)

        layout.addWidget(QLabel("确认新密码:"))
        self.confirm_pwd = QLineEdit()
        self.confirm_pwd.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.confirm_pwd)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("保存修改")
        ok_btn.clicked.connect(self.save_change)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def save_change(self):
        old = self.old_pwd.text()
        new1 = self.new_pwd.text()
        new2 = self.confirm_pwd.text()
        if not old or not new1 or not new2:
            QMessageBox.warning(self, "提示", "所有输入框不能为空！")
            return
        if new1 != new2:
            QMessageBox.warning(self, "提示", "两次输入的新密码不一致！")
            return
        if len(new1) < 4:
            QMessageBox.warning(self, "提示", "新密码长度至少4位！")
            return

        from database import get_connection
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM users WHERE id=?", (self.user_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            QMessageBox.warning(self, "错误", "找不到用户！")
            return
        stored_hash = row[0]

        if not auth.verify_password(old, stored_hash):
            QMessageBox.warning(self, "错误", "旧密码输入错误！")
            return

        new_hash = auth.hash_password(new1)
        if db_update_user_password(self.user_id, new_hash):
            QMessageBox.information(self, "成功", "用户密码修改成功！下次登录请使用新密码。")
            self.accept()
        else:
            QMessageBox.critical(self, "失败", "数据库更新失败！")

    def show_help(self):
        text = """【修改用户信息帮助】
1. 需要输入正确旧密码才能完成修改
2. 新密码长度至少4位
3. 修改登录密码，不会影响已经保存的网站密码
"""
        QMessageBox.information(self, "帮助", text)
