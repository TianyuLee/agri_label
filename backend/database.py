import sqlite3
import os
import hashlib
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "annotation.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # 用户表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_root BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 检查并添加 is_root 列（兼容旧数据库）
    try:
        cursor.execute("SELECT is_root FROM users LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE users ADD COLUMN is_root BOOLEAN DEFAULT 0")
        print("添加 is_root 列到 users 表")

    # 任务集合表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 任务表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_set_id INTEGER NOT NULL,
            query TEXT NOT NULL,
            completed BOOLEAN DEFAULT 0,
            completed_at TIMESTAMP,
            FOREIGN KEY (task_set_id) REFERENCES task_sets(id)
        )
    """)

    # rubric表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rubrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            selected BOOLEAN DEFAULT 0,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            version INTEGER DEFAULT 1,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
        )
    """)

    # 检查并添加 created_by 列（兼容旧数据库）
    try:
        cursor.execute("SELECT created_by FROM rubrics LIMIT 1")
    except sqlite3.OperationalError:
        # SQLite ALTER TABLE 不支持 DEFAULT CURRENT_TIMESTAMP，分步添加
        cursor.execute("ALTER TABLE rubrics ADD COLUMN created_by INTEGER")
        cursor.execute("ALTER TABLE rubrics ADD COLUMN created_at TIMESTAMP")
        # 为现有记录设置默认时间
        cursor.execute("UPDATE rubrics SET created_at = ? WHERE created_at IS NULL",
                       (datetime.now().isoformat(),))
        conn.commit()
        print("添加 created_by 和 created_at 列到 rubrics 表")

    # 检查并添加 version 列（兼容旧数据库）
    try:
        cursor.execute("SELECT version FROM rubrics LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE rubrics ADD COLUMN version INTEGER DEFAULT 1")
        # 为现有记录设置默认版本为1
        cursor.execute("UPDATE rubrics SET version = 1 WHERE version IS NULL")
        conn.commit()
        print("添加 version 列到 rubrics 表")

    # 用户任务分配表（记录哪些任务分配给哪些用户）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            task_id INTEGER NOT NULL,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
            UNIQUE(user_id, task_id)
        )
    """)

    # 标准答案表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reference_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            version INTEGER DEFAULT 1,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
        )
    """)

    # 检查并添加 version 列到 reference_answers 表（兼容旧数据库）
    try:
        cursor.execute("SELECT version FROM reference_answers LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE reference_answers ADD COLUMN version INTEGER DEFAULT 1")
        cursor.execute("UPDATE reference_answers SET version = 1 WHERE version IS NULL")
        conn.commit()
        print("添加 version 列到 reference_answers 表")

    # 插入示例数据
    cursor.execute("SELECT COUNT(*) FROM task_sets")
    if cursor.fetchone()[0] == 0:
        # 插入任务集合
        cursor.execute("INSERT INTO task_sets (name, description) VALUES (?, ?)",
                       ("农业病害标注", "关于农作物病害的问答标注任务"))
        task_set_id = cursor.lastrowid

        # 插入示例任务
        sample_tasks = [
            ("黄瓜得了炭疽病怎么防治",),
            ("番茄叶子发黄是什么原因",),
            ("水稻稻瘟病的治疗方法",),
            ("苹果树腐烂病如何处理",),
        ]

        sample_rubrics = [
            "包含具体的病害名称",
            "包含发病症状描述",
            "包含防治方法",
            "包含用药建议",
            "回答有科学依据",
            "语言通俗易懂",
        ]

        for task_data in sample_tasks:
            cursor.execute("INSERT INTO tasks (task_set_id, query) VALUES (?, ?)",
                           (task_set_id, task_data[0]))
            task_id = cursor.lastrowid

            for rubric_content in sample_rubrics:
                cursor.execute("INSERT INTO rubrics (task_id, content) VALUES (?, ?)",
                               (task_id, rubric_content))

    # 创建/更新 root 账号
    cursor.execute("SELECT id FROM users WHERE phone = 'root'")
    root_user = cursor.fetchone()
    if not root_user:
        hashed_root_pw = hashlib.sha256(b"root").hexdigest()
        cursor.execute("INSERT INTO users (phone, password, is_root) VALUES (?, ?, 1)",
                       ("root", hashed_root_pw))
        print("创建 root 账号成功")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("数据库初始化完成")
