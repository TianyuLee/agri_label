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

    # 检查并添加 created_at 列（独立的检查，因为之前的迁移可能只添加了 created_by）
    try:
        cursor.execute("SELECT created_at FROM rubrics LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE rubrics ADD COLUMN created_at TIMESTAMP")
        cursor.execute("UPDATE rubrics SET created_at = ? WHERE created_at IS NULL",
                       (datetime.now().isoformat(),))
        conn.commit()
        print("添加 created_at 列到 rubrics 表")

    # 检查并添加 version 列（兼容旧数据库）
    try:
        cursor.execute("SELECT version FROM rubrics LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE rubrics ADD COLUMN version INTEGER DEFAULT 1")
        # 为现有记录设置默认版本为1
        cursor.execute("UPDATE rubrics SET version = 1 WHERE version IS NULL")
        conn.commit()
        print("添加 version 列到 rubrics 表")

    # 用户任务集合分配表（记录哪些任务集合分配给哪些用户）
    # 一个任务集合可以分配给多个用户，这些用户共享该集合下的所有任务数据
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_task_sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            task_set_id INTEGER NOT NULL,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (task_set_id) REFERENCES task_sets(id) ON DELETE CASCADE,
            UNIQUE(user_id, task_set_id)
        )
    """)

    # 迁移旧数据：从 user_tasks 表迁移到 user_task_sets 表
    # 检查旧表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_tasks'")
    if cursor.fetchone():
        # 获取所有已分配的任务及其对应的任务集合
        cursor.execute("""
            SELECT DISTINCT ut.user_id, t.task_set_id
            FROM user_tasks ut
            JOIN tasks t ON t.id = ut.task_id
        """)
        old_assignments = cursor.fetchall()
        # 将数据迁移到新表
        for assignment in old_assignments:
            try:
                cursor.execute("""
                    INSERT INTO user_task_sets (user_id, task_set_id) VALUES (?, ?)
                """, (assignment[0], assignment[1]))
            except sqlite3.IntegrityError:
                pass  # 忽略重复项
        conn.commit()
        # 删除旧表
        cursor.execute("DROP TABLE user_tasks")
        conn.commit()
        print(f"迁移 {len(old_assignments)} 条任务分配到新表")

    # 保留旧表结构用于兼容（实际上不再需要，但为了代码迁移期使用）
    # 实际上上面的代码已经删除了旧表

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

    # 检查并添加 created_by 列到 reference_answers 表
    try:
        cursor.execute("SELECT created_by FROM reference_answers LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE reference_answers ADD COLUMN created_by INTEGER")
        conn.commit()
        print("添加 created_by 列到 reference_answers 表")

    # 检查并添加 created_at 列到 reference_answers 表
    try:
        cursor.execute("SELECT created_at FROM reference_answers LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE reference_answers ADD COLUMN created_at TIMESTAMP")
        cursor.execute("UPDATE reference_answers SET created_at = ? WHERE created_at IS NULL",
                       (datetime.now().isoformat(),))
        conn.commit()
        print("添加 created_at 列到 reference_answers 表")

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

    # 创建/更新 root 账号（使用符合新规则的账号名）
    ROOT_ACCOUNT = 'admin00'
    ROOT_PASSWORD = 'admin00'

    # 检查是否已存在新的 root 账号
    cursor.execute("SELECT id FROM users WHERE phone = ?", (ROOT_ACCOUNT,))
    root_user = cursor.fetchone()

    if not root_user:
        # 检查是否存在旧的 root 账号，如果存在则更新
        cursor.execute("SELECT id FROM users WHERE phone = 'root'")
        old_root = cursor.fetchone()
        if old_root:
            hashed_root_pw = hashlib.sha256(ROOT_PASSWORD.encode()).hexdigest()
            cursor.execute("UPDATE users SET phone = ?, password = ?, is_root = 1 WHERE id = ?",
                           (ROOT_ACCOUNT, hashed_root_pw, old_root[0]))
            print(f"更新 root 账号为: {ROOT_ACCOUNT}，密码: {ROOT_PASSWORD}")
        else:
            # 创建新的 root 账号
            hashed_root_pw = hashlib.sha256(ROOT_PASSWORD.encode()).hexdigest()
            cursor.execute("INSERT INTO users (phone, password, is_root) VALUES (?, ?, 1)",
                           (ROOT_ACCOUNT, hashed_root_pw))
            print(f"创建 root 账号成功: {ROOT_ACCOUNT}，密码: {ROOT_PASSWORD}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("数据库初始化完成")
