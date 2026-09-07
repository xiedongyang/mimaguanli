from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QMessageBox, QCheckBox
)
from database import check_credentials, create_user
import hashlib
import os
import hmac
from PyQt5.QtCore import Qt


def hash_password(password: str) -> str:
    """对明文密码做PBKDF2加盐哈希，返回 salt$hash 格式字符串"""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100000
    )
    return salt.hex() + "$" + key.hex()


def verify_password(password: str, stored_hash: str) -> bool:
    """校验明文密码和数据库存储的hash是否匹配"""
    try:
        salt_hex, key_hex = stored_hash.split("$")
        salt = bytes.fromhex(salt_hex)
        stored_key = bytes.fromhex(key_hex)
        derived_key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            100000
        )
        return hmac.compare_digest(derived_key, stored_key)
    except Exception:
        return False


class AuthWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("密码管理器 - 登录/注册")
        self.setFixedSize(400, 330)
        self._username = ""
        self.init_ui()

    @property
    def current_username(self):
        return self._username

    def init_ui(self):
        layout = QVBoxLayout()
        self.username_label = QLabel("用户名:")
        self.username_input = QLineEdit()
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)

        self.password_label = QLabel("密码:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)

        # ============新增登录提示【在这里插入】============
        tip_label = QLabel('<span style="color:#444444; font-size:14px;">提示：首次使用请勾选注册新用户；密码本地加密保存，遗忘登录密码无法恢复数据</span>')
        tip_label.setWordWrap(True)
        tip_label.setContentsMargins(0, 8, 0, 8)  # 上下增加边距，不挤输入框和复选框
        tip_label.setWordWrap(True)  # 文字自动换行
        layout.addWidget(tip_label)

        self.register_checkbox = QCheckBox("注册新用户")
        self.register_checkbox.stateChanged.connect(self.update_button_text)
        layout.addWidget(self.register_checkbox)

        self.login_button = QPushButton("登录")
        self.login_button.clicked.connect(self.handle_auth)
        layout.addWidget(self.login_button)
        self.setLayout(layout)

    def update_button_text(self, state):
        self.login_button.setText("注册" if state else "登录")

    def handle_auth(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        if not username or not password:
            QMessageBox.warning(self, "错误", "用户名和密码不能为空!")
            return

        if self.register_checkbox.isChecked():
            hashed_password = hash_password(password)
            if create_user(username, hashed_password):
                QMessageBox.information(self, "成功", "用户注册成功，请登录!")
                self.password_input.clear()
                self.register_checkbox.setChecked(False)
            else:
                QMessageBox.warning(self, "错误", "用户名已存在!")
        else:
            stored_hash = check_credentials(username)
            if stored_hash and verify_password(password, stored_hash):
                self._username = username
                self.accept()
            else:
                QMessageBox.warning(self, "错误", "用户名或密码错误!")
