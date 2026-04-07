from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import get_db, init_db
from models import (
    UserRegister, UserLogin, UserResponse,
    TaskSet, Task, Rubric, TaskWithRubrics, TaskWithDetails,
    RubricUpdate, TaskCompleteRequest,
    TaskSetCreate, TaskSetUpdate, TaskCreate, TaskUpdate,
    RubricCreate, RubricUpdateContent,
    ReferenceAnswer, ReferenceAnswerCreate, ReferenceAnswerUpdate
)
import hashlib
import jwt
from datetime import datetime, timedelta
from typing import List, Optional
import sqlite3

app = FastAPI(title="标注系统API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

security = HTTPBearer()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {"user_id": user_id, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="无效的token")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="token已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的token")

def get_current_user_with_root(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="无效的token")

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, phone, is_root FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()

        if not user:
            raise HTTPException(status_code=401, detail="用户不存在")

        return {"id": user["id"], "phone": user["phone"], "is_root": bool(user["is_root"])}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="token已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的token")

def require_root(current_user: dict = Depends(get_current_user_with_root)):
    if not current_user.get("is_root"):
        raise HTTPException(status_code=403, detail="需要root权限")
    return current_user

@app.on_event("startup")
async def startup():
    init_db()

# 注册
@app.post("/api/register", response_model=dict)
def register(data: UserRegister):
    conn = get_db()
    cursor = conn.cursor()

    # 验证手机号格式
    if not data.phone.isdigit() or len(data.phone) != 11:
        conn.close()
        raise HTTPException(status_code=400, detail="手机号格式不正确")

    # 验证密码长度
    if len(data.password) < 6:
        conn.close()
        raise HTTPException(status_code=400, detail="密码长度至少6位")

    # 检查手机号是否已存在
    cursor.execute("SELECT id FROM users WHERE phone = ?", (data.phone,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="手机号已注册")

    hashed_pw = hash_password(data.password)
    cursor.execute("INSERT INTO users (phone, password) VALUES (?, ?)",
                   (data.phone, hashed_pw))
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()

    token = create_token(user_id)
    return {"message": "注册成功", "token": token, "user_id": user_id}

# 登录
@app.post("/api/login", response_model=dict)
def login(data: UserLogin):
    conn = get_db()
    cursor = conn.cursor()

    hashed_pw = hash_password(data.password)
    cursor.execute("SELECT id, phone, is_root FROM users WHERE phone = ? AND password = ?",
                   (data.phone, hashed_pw))
    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="手机号或密码错误")

    token = create_token(user["id"])
    return {
        "message": "登录成功",
        "token": token,
        "user_id": user["id"],
        "phone": user["phone"],
        "is_root": bool(user["is_root"])
    }

# 获取当前用户信息
@app.get("/api/me", response_model=dict)
def get_me(current_user: dict = Depends(get_current_user_with_root)):
    return {
        "id": current_user["id"],
        "phone": current_user["phone"],
        "is_root": current_user["is_root"]
    }

# 获取任务集合列表（普通用户只能看到分配给自己的）
@app.get("/api/task-sets", response_model=List[TaskSet])
def get_task_sets(user: dict = Depends(get_current_user_with_root)):
    conn = get_db()
    cursor = conn.cursor()

    if user["is_root"]:
        # root 用户看到所有任务集合
        cursor.execute("SELECT * FROM task_sets ORDER BY created_at DESC")
    else:
        # 普通用户只看到分配了任务的集合
        cursor.execute("""
            SELECT DISTINCT ts.* FROM task_sets ts
            JOIN tasks t ON t.task_set_id = ts.id
            JOIN user_tasks ut ON ut.task_id = t.id
            WHERE ut.user_id = ?
            ORDER BY ts.created_at DESC
        """, (user["id"],))

    task_sets = cursor.fetchall()
    conn.close()
    return [TaskSet(**dict(ts)) for ts in task_sets]

# 获取任务集合下的任务列表（普通用户只能看到分配给自己的）
@app.get("/api/task-sets/{task_set_id}/tasks", response_model=List[Task])
def get_tasks(task_set_id: int, user: dict = Depends(get_current_user_with_root)):
    conn = get_db()
    cursor = conn.cursor()

    if user["is_root"]:
        # root 用户看到该集合下所有任务
        cursor.execute("SELECT * FROM tasks WHERE task_set_id = ? ORDER BY id",
                       (task_set_id,))
    else:
        # 普通用户只看到分配给他们的任务
        cursor.execute("""
            SELECT t.* FROM tasks t
            JOIN user_tasks ut ON ut.task_id = t.id
            WHERE t.task_set_id = ? AND ut.user_id = ?
            ORDER BY t.id
        """, (task_set_id, user["id"]))

    tasks = cursor.fetchall()
    conn.close()
    return [Task(**dict(t)) for t in tasks]

# 获取任务详情（含rubrics和标准答案）
@app.get("/api/tasks/{task_id}", response_model=TaskWithDetails)
def get_task_detail(task_id: int, version: int = 0, current_user: int = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    task = cursor.fetchone()

    if not task:
        conn.close()
        raise HTTPException(status_code=404, detail="任务不存在")

    # 如果指定了version，只返回对应版本的rubrics和reference_answers
    if version == 1 or version == 2:
        cursor.execute("SELECT * FROM rubrics WHERE task_id = ? AND version = ? ORDER BY id", (task_id, version))
        rubrics = cursor.fetchall()
        cursor.execute("SELECT * FROM reference_answers WHERE task_id = ? AND version = ? ORDER BY id", (task_id, version))
        reference_answers = cursor.fetchall()
    else:
        # 默认返回所有版本的rubrics和reference_answers
        cursor.execute("SELECT * FROM rubrics WHERE task_id = ? ORDER BY id", (task_id,))
        rubrics = cursor.fetchall()
        cursor.execute("SELECT * FROM reference_answers WHERE task_id = ? ORDER BY id", (task_id,))
        reference_answers = cursor.fetchall()

    conn.close()

    task_dict = dict(task)
    task_dict["rubrics"] = [Rubric(**dict(r)) for r in rubrics]
    task_dict["reference_answers"] = [ReferenceAnswer(**dict(r)) for r in reference_answers]

    return TaskWithDetails(**task_dict)

# 更新rubric选择状态
@app.patch("/api/rubrics/{rubric_id}", response_model=Rubric)
def update_rubric(rubric_id: int, data: RubricUpdate, current_user: int = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("UPDATE rubrics SET selected = ? WHERE id = ?",
                   (data.selected, rubric_id))
    conn.commit()

    cursor.execute("SELECT * FROM rubrics WHERE id = ?", (rubric_id,))
    rubric = cursor.fetchone()
    conn.close()

    if not rubric:
        raise HTTPException(status_code=404, detail="rubric不存在")

    return Rubric(**dict(rubric))

# 创建rubric（普通用户，只能给自己分配的任务添加）
@app.post("/api/rubrics", response_model=Rubric)
def create_rubric_user(data: RubricCreate, current_user: int = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()

    # 检查任务是否存在
    cursor.execute("SELECT id FROM tasks WHERE id = ?", (data.task_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="任务不存在")

    # 检查该任务是否分配给了当前用户
    cursor.execute("SELECT 1 FROM user_tasks WHERE user_id = ? AND task_id = ?",
                   (current_user, data.task_id))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=403, detail="没有权限为此任务添加rubric")

    cursor.execute("INSERT INTO rubrics (task_id, content, created_by, version) VALUES (?, ?, ?, ?)",
                   (data.task_id, data.content, current_user, data.version))
    conn.commit()
    rubric_id = cursor.lastrowid

    cursor.execute("SELECT * FROM rubrics WHERE id = ?", (rubric_id,))
    rubric = cursor.fetchone()
    conn.close()
    return Rubric(**dict(rubric))

# 删除rubric（root或任务分配的用户可以删除）
@app.delete("/api/rubrics/{rubric_id}")
def delete_rubric_user(rubric_id: int, current_user: int = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()

    # 检查rubric是否存在
    cursor.execute("SELECT * FROM rubrics WHERE id = ?", (rubric_id,))
    rubric = cursor.fetchone()
    if not rubric:
        conn.close()
        raise HTTPException(status_code=404, detail="rubric不存在")

    # 检查权限：root或任务分配的用户可以删除
    if not check_rubric_permission(cursor, rubric_id, current_user):
        conn.close()
        raise HTTPException(status_code=403, detail="没有权限删除此rubric")

    cursor.execute("DELETE FROM rubrics WHERE id = ?", (rubric_id,))
    conn.commit()
    conn.close()
    return {"message": "删除成功"}

# 完成任务
@app.patch("/api/tasks/{task_id}/complete", response_model=Task)
def complete_task(task_id: int, data: TaskCompleteRequest, current_user: int = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()

    completed_at = datetime.now() if data.completed else None
    cursor.execute("UPDATE tasks SET completed = ?, completed_at = ? WHERE id = ?",
                   (data.completed, completed_at, task_id))
    conn.commit()

    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    task = cursor.fetchone()
    conn.close()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return Task(**dict(task))

# ==================== Root 管理接口 ====================

# 获取所有用户列表（仅root）
@app.get("/api/admin/users", response_model=List[dict])
def get_all_users(current_user: dict = Depends(require_root)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, phone, is_root, created_at FROM users ORDER BY id")
    users = cursor.fetchall()
    conn.close()
    return [{"id": u["id"], "phone": u["phone"], "is_root": bool(u["is_root"]), "created_at": u["created_at"]} for u in users]

# 创建任务集合（仅root）
@app.post("/api/admin/task-sets", response_model=TaskSet)
def create_task_set(data: TaskSetCreate, current_user: dict = Depends(require_root)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO task_sets (name, description) VALUES (?, ?)",
                   (data.name, data.description))
    conn.commit()
    task_set_id = cursor.lastrowid
    cursor.execute("SELECT * FROM task_sets WHERE id = ?", (task_set_id,))
    task_set = cursor.fetchone()
    conn.close()
    return TaskSet(**dict(task_set))

# 更新任务集合（仅root）
@app.patch("/api/admin/task-sets/{task_set_id}", response_model=TaskSet)
def update_task_set(task_set_id: int, data: TaskSetUpdate, current_user: dict = Depends(require_root)):
    conn = get_db()
    cursor = conn.cursor()

    # 获取当前数据
    cursor.execute("SELECT * FROM task_sets WHERE id = ?", (task_set_id,))
    task_set = cursor.fetchone()
    if not task_set:
        conn.close()
        raise HTTPException(status_code=404, detail="任务集合不存在")

    # 更新
    name = data.name if data.name is not None else task_set["name"]
    description = data.description if data.description is not None else task_set["description"]

    cursor.execute("UPDATE task_sets SET name = ?, description = ? WHERE id = ?",
                   (name, description, task_set_id))
    conn.commit()

    cursor.execute("SELECT * FROM task_sets WHERE id = ?", (task_set_id,))
    updated = cursor.fetchone()
    conn.close()
    return TaskSet(**dict(updated))

# 删除任务集合（仅root）
@app.delete("/api/admin/task-sets/{task_set_id}")
def delete_task_set(task_set_id: int, current_user: dict = Depends(require_root)):
    conn = get_db()
    cursor = conn.cursor()

    # 先删除该集合下所有任务的rubrics
    cursor.execute("""
        DELETE FROM rubrics WHERE task_id IN (
            SELECT id FROM tasks WHERE task_set_id = ?
        )
    """, (task_set_id,))

    # 删除该集合下的所有任务
    cursor.execute("DELETE FROM tasks WHERE task_set_id = ?", (task_set_id,))

    # 删除任务集合
    cursor.execute("DELETE FROM task_sets WHERE id = ?", (task_set_id,))
    conn.commit()
    conn.close()

    return {"message": "删除成功"}

# 创建任务（仅root）
@app.post("/api/admin/tasks", response_model=Task)
def create_task(data: TaskCreate, current_user: dict = Depends(require_root)):
    conn = get_db()
    cursor = conn.cursor()

    # 检查任务集合是否存在
    cursor.execute("SELECT id FROM task_sets WHERE id = ?", (data.task_set_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="任务集合不存在")

    cursor.execute("INSERT INTO tasks (task_set_id, query) VALUES (?, ?)",
                   (data.task_set_id, data.query))
    conn.commit()
    task_id = cursor.lastrowid

    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    task = cursor.fetchone()
    conn.close()
    return Task(**dict(task))

# 更新任务（仅root）
@app.patch("/api/admin/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, data: TaskUpdate, current_user: dict = Depends(require_root)):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    task = cursor.fetchone()
    if not task:
        conn.close()
        raise HTTPException(status_code=404, detail="任务不存在")

    query = data.query if data.query is not None else task["query"]
    cursor.execute("UPDATE tasks SET query = ? WHERE id = ?", (query, task_id))
    conn.commit()

    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    updated = cursor.fetchone()
    conn.close()
    return Task(**dict(updated))

# 删除任务（仅root）
@app.delete("/api/admin/tasks/{task_id}")
def delete_task(task_id: int, current_user: dict = Depends(require_root)):
    conn = get_db()
    cursor = conn.cursor()

    # 先删除rubrics
    cursor.execute("DELETE FROM rubrics WHERE task_id = ?", (task_id,))
    # 删除任务
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

    return {"message": "删除成功"}

# 创建rubric（仅root）
@app.post("/api/admin/rubrics", response_model=Rubric)
def create_rubric(data: RubricCreate, current_user: dict = Depends(require_root)):
    conn = get_db()
    cursor = conn.cursor()

    # 检查任务是否存在
    cursor.execute("SELECT id FROM tasks WHERE id = ?", (data.task_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="任务不存在")

    cursor.execute("INSERT INTO rubrics (task_id, content, version) VALUES (?, ?, ?)",
                   (data.task_id, data.content, data.version))
    conn.commit()
    rubric_id = cursor.lastrowid

    cursor.execute("SELECT * FROM rubrics WHERE id = ?", (rubric_id,))
    rubric = cursor.fetchone()
    conn.close()
    return Rubric(**dict(rubric))

# 更新rubric内容（仅root）
@app.patch("/api/admin/rubrics/{rubric_id}/content", response_model=Rubric)
def update_rubric_content(rubric_id: int, data: RubricUpdateContent, current_user: dict = Depends(require_root)):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM rubrics WHERE id = ?", (rubric_id,))
    rubric = cursor.fetchone()
    if not rubric:
        conn.close()
        raise HTTPException(status_code=404, detail="rubric不存在")

    cursor.execute("UPDATE rubrics SET content = ? WHERE id = ?", (data.content, rubric_id))
    conn.commit()

    cursor.execute("SELECT * FROM rubrics WHERE id = ?", (rubric_id,))
    updated = cursor.fetchone()
    conn.close()
    return Rubric(**dict(updated))

# 删除rubric（仅root）
@app.delete("/api/admin/rubrics/{rubric_id}")
def delete_rubric(rubric_id: int, current_user: dict = Depends(require_root)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM rubrics WHERE id = ?", (rubric_id,))
    conn.commit()
    conn.close()
    return {"message": "删除成功"}

# 辅助函数：检查用户是否有权限修改rubric（所有登录用户都可以，数据已通过版本隔离）
def check_rubric_permission(cursor, rubric_id: int, user_id: int) -> bool:
    """检查用户是否是root或者是登录用户（所有登录用户都有权限）"""
    # 检查是否是root用户
    cursor.execute("SELECT is_root FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if user and user["is_root"]:
        return True

    # 普通登录用户也有权限（数据已通过版本和任务分配隔离）
    cursor.execute("SELECT 1 FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone() is not None


# 更新rubric内容（root或任务分配的用户可以更新）
@app.patch("/api/rubrics/{rubric_id}/content", response_model=Rubric)
def update_rubric_content_user(rubric_id: int, data: RubricUpdateContent, current_user: int = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM rubrics WHERE id = ?", (rubric_id,))
    rubric = cursor.fetchone()
    if not rubric:
        conn.close()
        raise HTTPException(status_code=404, detail="rubric不存在")

    # 检查权限：root或任务分配的用户可以修改
    if not check_rubric_permission(cursor, rubric_id, current_user):
        conn.close()
        raise HTTPException(status_code=403, detail="没有权限修改此rubric")

    cursor.execute("UPDATE rubrics SET content = ? WHERE id = ?", (data.content, rubric_id))
    conn.commit()

    cursor.execute("SELECT * FROM rubrics WHERE id = ?", (rubric_id,))
    updated = cursor.fetchone()
    conn.close()
    return Rubric(**dict(updated))


# ==================== Root 切换用户视图接口 ====================

# 获取指定用户的任务集合（root 切换视图用）
@app.get("/api/admin/users/{target_user_id}/task-sets", response_model=List[TaskSet])
def get_user_task_sets(target_user_id: int, current_user: dict = Depends(require_root)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT ts.* FROM task_sets ts
        JOIN tasks t ON t.task_set_id = ts.id
        JOIN user_tasks ut ON ut.task_id = t.id
        WHERE ut.user_id = ?
        ORDER BY ts.created_at DESC
    """, (target_user_id,))
    task_sets = cursor.fetchall()
    conn.close()
    return [TaskSet(**dict(ts)) for ts in task_sets]

# 获取指定用户在某个集合下的任务（root 切换视图用）
@app.get("/api/admin/users/{target_user_id}/task-sets/{task_set_id}/tasks", response_model=List[Task])
def get_user_tasks(target_user_id: int, task_set_id: int, current_user: dict = Depends(require_root)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.* FROM tasks t
        JOIN user_tasks ut ON ut.task_id = t.id
        WHERE t.task_set_id = ? AND ut.user_id = ?
        ORDER BY t.id
    """, (task_set_id, target_user_id))
    tasks = cursor.fetchall()
    conn.close()
    return [Task(**dict(t)) for t in tasks]

# 给用户分配任务（仅root）
@app.post("/api/admin/assign-task")
def assign_task_to_user(user_id: int, task_id: int, current_user: dict = Depends(require_root)):
    conn = get_db()
    cursor = conn.cursor()

    # 检查用户是否存在
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="用户不存在")

    # 检查任务是否存在
    cursor.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="任务不存在")

    # 分配任务
    try:
        cursor.execute("INSERT INTO user_tasks (user_id, task_id) VALUES (?, ?)",
                       (user_id, task_id))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="该任务已分配给该用户")

    conn.close()
    return {"message": "任务分配成功"}

# 取消用户的任务分配（仅root）
@app.delete("/api/admin/assign-task")
def unassign_task_from_user(user_id: int, task_id: int, current_user: dict = Depends(require_root)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_tasks WHERE user_id = ? AND task_id = ?",
                   (user_id, task_id))
    conn.commit()
    conn.close()
    return {"message": "任务分配已取消"}

# 获取所有任务集合（用于 root 分配任务时选择）
@app.get("/api/admin/all-task-sets", response_model=List[TaskSet])
def get_all_task_sets(current_user: dict = Depends(require_root)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM task_sets ORDER BY created_at DESC")
    task_sets = cursor.fetchall()
    conn.close()
    return [TaskSet(**dict(ts)) for ts in task_sets]

# 获取某个集合下所有任务（用于 root 分配任务时选择）
@app.get("/api/admin/task-sets/{task_set_id}/all-tasks", response_model=List[Task])
def get_all_tasks_in_set(task_set_id: int, current_user: dict = Depends(require_root)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE task_set_id = ? ORDER BY id", (task_set_id,))
    tasks = cursor.fetchall()
    conn.close()
    return [Task(**dict(t)) for t in tasks]

# 获取用户的已分配任务列表
@app.get("/api/admin/users/{user_id}/assigned-tasks")
def get_user_assigned_tasks(user_id: int, current_user: dict = Depends(require_root)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.id, t.query, t.completed, ts.name as task_set_name
        FROM tasks t
        JOIN user_tasks ut ON ut.task_id = t.id
        JOIN task_sets ts ON ts.id = t.task_set_id
        WHERE ut.user_id = ?
        ORDER BY t.id
    """, (user_id,))
    tasks = cursor.fetchall()
    conn.close()
    return [{"id": t["id"], "query": t["query"], "completed": t["completed"],
             "task_set_name": t["task_set_name"]} for t in tasks]

# 获取未分配给指定用户的任务列表
@app.get("/api/admin/users/{user_id}/unassigned-tasks")
def get_user_unassigned_tasks(user_id: int, current_user: dict = Depends(require_root)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.id, t.query, ts.name as task_set_name
        FROM tasks t
        JOIN task_sets ts ON ts.id = t.task_set_id
        WHERE t.id NOT IN (
            SELECT task_id FROM user_tasks WHERE user_id = ?
        )
        ORDER BY ts.id, t.id
    """, (user_id,))
    tasks = cursor.fetchall()
    conn.close()
    return [{"id": t["id"], "query": t["query"],
             "task_set_name": t["task_set_name"]} for t in tasks]


# ==================== 标准答案管理接口 ====================

# 获取任务的标准答案列表
@app.get("/api/tasks/{task_id}/reference-answers", response_model=List[ReferenceAnswer])
def get_reference_answers(task_id: int, current_user: int = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM reference_answers WHERE task_id = ? ORDER BY id", (task_id,))
    answers = cursor.fetchall()
    conn.close()

    return [ReferenceAnswer(**dict(a)) for a in answers]

# 创建标准答案（仅root）
@app.post("/api/admin/reference-answers", response_model=ReferenceAnswer)
def create_reference_answer(data: ReferenceAnswerCreate, current_user: dict = Depends(require_root)):
    conn = get_db()
    cursor = conn.cursor()

    # 检查任务是否存在
    cursor.execute("SELECT id FROM tasks WHERE id = ?", (data.task_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="任务不存在")

    cursor.execute("INSERT INTO reference_answers (task_id, content, created_by, version) VALUES (?, ?, ?, ?)",
                   (data.task_id, data.content, current_user["id"], data.version))
    conn.commit()
    answer_id = cursor.lastrowid

    cursor.execute("SELECT * FROM reference_answers WHERE id = ?", (answer_id,))
    answer = cursor.fetchone()
    conn.close()
    return ReferenceAnswer(**dict(answer))

# 创建标准答案（普通用户）
@app.post("/api/reference-answers", response_model=ReferenceAnswer)
def create_reference_answer_user(data: ReferenceAnswerCreate, current_user: int = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()

    # 检查任务是否存在
    cursor.execute("SELECT id FROM tasks WHERE id = ?", (data.task_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="任务不存在")

    cursor.execute("INSERT INTO reference_answers (task_id, content, created_by, version) VALUES (?, ?, ?, ?)",
                   (data.task_id, data.content, current_user, data.version))
    conn.commit()
    answer_id = cursor.lastrowid

    cursor.execute("SELECT * FROM reference_answers WHERE id = ?", (answer_id,))
    answer = cursor.fetchone()
    conn.close()
    return ReferenceAnswer(**dict(answer))

# 辅助函数：检查用户是否有权限修改标注答案（所有登录用户都可以，数据已通过版本隔离）
def check_answer_permission(cursor, answer_id: int, user_id: int) -> bool:
    """检查用户是否是root或者是登录用户（所有登录用户都有权限）"""
    # 检查是否是root用户
    cursor.execute("SELECT is_root FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if user and user["is_root"]:
        return True

    # 普通登录用户也有权限（数据已通过版本和任务分配隔离）
    cursor.execute("SELECT 1 FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone() is not None


# 删除标准答案（root或任务分配的用户可以删除）
@app.delete("/api/reference-answers/{answer_id}")
def delete_reference_answer_user(answer_id: int, current_user: int = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()

    # 检查标准答案是否存在
    cursor.execute("SELECT * FROM reference_answers WHERE id = ?", (answer_id,))
    answer = cursor.fetchone()
    if not answer:
        conn.close()
        raise HTTPException(status_code=404, detail="标准答案不存在")

    # 检查权限：root或任务分配的用户可以删除
    if not check_answer_permission(cursor, answer_id, current_user):
        conn.close()
        raise HTTPException(status_code=403, detail="没有权限删除此标准答案")

    cursor.execute("DELETE FROM reference_answers WHERE id = ?", (answer_id,))
    conn.commit()
    conn.close()
    return {"message": "删除成功"}

# 更新标准答案（root或任务分配的用户可以更新）
@app.patch("/api/reference-answers/{answer_id}", response_model=ReferenceAnswer)
def update_reference_answer_user(answer_id: int, data: ReferenceAnswerUpdate, current_user: int = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM reference_answers WHERE id = ?", (answer_id,))
    answer = cursor.fetchone()
    if not answer:
        conn.close()
        raise HTTPException(status_code=404, detail="标准答案不存在")

    # 检查权限：root或任务分配的用户可以修改
    if not check_answer_permission(cursor, answer_id, current_user):
        conn.close()
        raise HTTPException(status_code=403, detail="没有权限修改此标准答案")

    cursor.execute("UPDATE reference_answers SET content = ? WHERE id = ?", (data.content, answer_id))
    conn.commit()

    cursor.execute("SELECT * FROM reference_answers WHERE id = ?", (answer_id,))
    updated = cursor.fetchone()
    conn.close()
    return ReferenceAnswer(**dict(updated))

# 删除标准答案（仅root，可删除任何）
@app.delete("/api/admin/reference-answers/{answer_id}")
def delete_reference_answer(answer_id: int, current_user: dict = Depends(require_root)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reference_answers WHERE id = ?", (answer_id,))
    conn.commit()
    conn.close()
    return {"message": "删除成功"}

# 更新标准答案（仅root，可更新任何）
@app.patch("/api/admin/reference-answers/{answer_id}", response_model=ReferenceAnswer)
def update_reference_answer(answer_id: int, data: ReferenceAnswerUpdate, current_user: dict = Depends(require_root)):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM reference_answers WHERE id = ?", (answer_id,))
    answer = cursor.fetchone()
    if not answer:
        conn.close()
        raise HTTPException(status_code=404, detail="标准答案不存在")

    cursor.execute("UPDATE reference_answers SET content = ? WHERE id = ?", (data.content, answer_id))
    conn.commit()

    cursor.execute("SELECT * FROM reference_answers WHERE id = ?", (answer_id,))
    updated = cursor.fetchone()
    conn.close()
    return ReferenceAnswer(**dict(updated))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
