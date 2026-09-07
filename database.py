import sqlite3
from datetime import datetime
# 数据库文件名称
DB_NAME = "password_manager.db"


def get_connection():
    """获取数据库连接，设置外键支持"""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database():
    """
    初始化数据库，创建所需的表
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 创建用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')

        # 创建分组表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                group_name TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                UNIQUE(user_id, group_name)
            )
        ''')

        # 创建密码表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS passwords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                group_id INTEGER,
                site_name TEXT NOT NULL,
                site_url TEXT,
                username TEXT NOT NULL,
                enc_password TEXT NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (group_id) REFERENCES groups (id) ON DELETE SET NULL
            )
        ''')
        conn.commit()
    except sqlite3.Error as e:
        print(f"数据库初始化错误: {e}")
    finally:
        conn.close()

# ================= 用户认证相关 =================

def create_user(username, password_hash):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    except sqlite3.Error as e:
        print(f"创建用户错误: {e}")
        return False
    finally:
        conn.close()


def check_credentials(username):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        print(f"查询凭证错误: {e}")
        return None
    finally:
        conn.close()


def get_user_id(username):
    """根据用户名获取用户ID"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        print(f"获取用户ID错误: {e}")
        return None
    finally:
        conn.close()



# ================= 分组管理相关 =================

def get_groups(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT id, group_name FROM groups WHERE user_id = ? ORDER BY group_name', (user_id,))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"获取分组错误: {e}")
        return []
    finally:
        conn.close()


def get_group_id(user_id, group_name):
    """根据用户ID和分组名获取分组ID"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT id FROM groups WHERE user_id = ? AND group_name = ?', (user_id, group_name))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        print(f"获取分组ID错误: {e}")
        return None
    finally:
        conn.close()


def add_group(user_id, group_name):
    """添加新分组"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO groups (user_id, group_name)
            VALUES (?, ?)
        ''', (user_id, group_name))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # 捕获唯一约束冲突
        return False
    except sqlite3.Error as e:
        print(f"添加分组数据库错误: {e}")
        return False
    finally:
        conn.close()

def update_group_name(group_id, new_group_name):
    """修改分组名称"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE groups
            SET group_name = ?
            WHERE id = ?
        ''', (new_group_name, group_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # 重名触发唯一约束
        return False
    except sqlite3.Error as e:
        print(f"修改分组名称错误: {e}")
        return False
    finally:
        conn.close()



def delete_selected_group(group_id):
    """
    删除分组 (数据库外键会自动将该分组下的密码设为未分组)
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM groups WHERE id = ?', (group_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"删除分组错误: {e}")
        return False
    finally:
        conn.close()


# ================= 密码记录管理相关 =================

def add_password(user_id, group_id, site_name, site_url, username, enc_password, notes):
    conn = get_connection()
    cur = conn.cursor()
    # ✅Python获取本地北京时间，写入数据库，不再依赖SQLite CURRENT_TIMESTAMP
    now_local = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = """
    INSERT INTO passwords(user_id,group_id,site_name,site_url,username,enc_password,notes,created_at)
    VALUES (?,?,?,?,?,?,?,?)
    """
    cur.execute(sql,(user_id,group_id,site_name,site_url,username,enc_password,notes, now_local))
    conn.commit()
    ok = cur.rowcount > 0
    conn.close()
    return ok


def get_passwords(user_id, group_id=None):
    """
    获取密码列表。
    如果提供 group_id，则获取该分组下的密码；否则获取该用户所有密码。
    返回列表格式: [(id, site_name, site_url, username, enc_password, notes, created_at), ...]
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if group_id is not None:
            cursor.execute('''
                SELECT id, site_name, site_url, username, enc_password, notes, created_at
                FROM passwords WHERE user_id = ? AND group_id = ? ORDER BY created_at DESC
            ''', (user_id, group_id))
        else:
            cursor.execute('''
                SELECT id, site_name, site_url, username, enc_password, notes, created_at
                FROM passwords WHERE user_id = ? ORDER BY created_at DESC
            ''', (user_id,))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"获取密码列表错误: {e}")
        return []
    finally:
        conn.close()


def get_password_details(password_id):
    """根据密码记录ID获取单条密码的详细信息"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT id, group_id, site_name, site_url, username, enc_password, notes
            FROM passwords WHERE id = ?
        ''', (password_id,))
        return cursor.fetchone()
    except sqlite3.Error as e:
        print(f"获取密码详情错误: {e}")
        return None
    finally:
        conn.close()


def update_password(password_id, group_id, site_name, site_url, username, enc_password, notes):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE passwords
            SET group_id = ?, site_name = ?, site_url = ?, username = ?, enc_password = ?, notes = ?
            WHERE id = ?
        ''', (group_id, site_name, site_url, username, enc_password, notes, password_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"更新密码记录错误: {e}")
        return False
    finally:
        conn.close()

def update_user_password(user_id:int, new_password_hash:str):
    """更新用户密码哈希"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE users SET password_hash = ? WHERE id = ?
        ''',(new_password_hash, user_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"更新用户密码错误:{e}")
        return False
    finally:
        conn.close()


def delete_password(password_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM passwords WHERE id = ?', (password_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"删除密码记录错误: {e}")
        return False
    finally:
        conn.close()
