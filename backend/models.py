from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class UserRegister(BaseModel):
    phone: str
    password: str

class UserLogin(BaseModel):
    phone: str
    password: str

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

class UserResponse(BaseModel):
    id: int
    phone: str
    is_root: bool = False
    created_at: datetime

    class Config:
        from_attributes = True

class TaskSet(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class Task(BaseModel):
    id: int
    task_set_id: int
    query: str
    completed: bool
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

class Rubric(BaseModel):
    id: int
    task_id: int
    content: str
    selected: bool
    created_by: Optional[int] = None
    version: int = 1

    class Config:
        from_attributes = True

class RubricUpdate(BaseModel):
    selected: bool

class TaskWithRubrics(BaseModel):
    id: int
    task_set_id: int
    query: str
    completed: bool
    completed_at: Optional[datetime]
    rubrics: List[Rubric]

    class Config:
        from_attributes = True

class TaskCompleteRequest(BaseModel):
    completed: bool

# Root 用户管理模型
class TaskSetCreate(BaseModel):
    name: str
    description: Optional[str] = None

class TaskSetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class TaskCreate(BaseModel):
    task_set_id: int
    query: str

class TaskUpdate(BaseModel):
    query: Optional[str] = None

class RubricCreate(BaseModel):
    task_id: int
    content: str
    version: int = 1  # 1=V1版本, 2=V2版本
    selected: bool = False  # 是否勾选

class RubricUpdateContent(BaseModel):
    content: str

# 标准答案模型
class ReferenceAnswer(BaseModel):
    id: int
    task_id: int
    content: str
    created_by: Optional[int] = None
    version: int = 1

    class Config:
        from_attributes = True

class ReferenceAnswerCreate(BaseModel):
    task_id: int
    content: str
    version: int = 1  # 1=V1版本, 2=V2版本

class ReferenceAnswerUpdate(BaseModel):
    content: str

# Tree 相关模型
class TreeRubric(BaseModel):
    criterion: str
    score: int = 0

class TreeNodeData(BaseModel):
    """返回给前端的树节点数据"""
    id: int
    claim: str
    type: str  # 'branch' 或 'leaf'
    rubrics: List[TreeRubric] = []
    nodes: List['TreeNodeData'] = []
    selected: bool = False  # 用户选择状态
    professional: bool = False  # 专业性标记
    required: bool = False  # 必答标记

class TaskWithDetails(BaseModel):
    id: int
    task_set_id: int
    query: str
    completed: bool
    completed_at: Optional[datetime]
    rubrics: List[Rubric]
    reference_answers: List[ReferenceAnswer]
    tree: Optional[TreeNodeData] = None  # 树形结构

    class Config:
        from_attributes = True

class TreeNode(BaseModel):
    claim: str
    type: str  # 'branch' 或 'leaf'
    rubrics: List[TreeRubric] = []
    nodes: List['TreeNode'] = []  # 子节点

class ImportTree(BaseModel):
    reason: str = ""
    tree: Optional[TreeNode] = None

# 批量导入模型
class ImportRubric(BaseModel):
    criterion: str
    axis: str = ""
    point: int = 0
    selected: bool = False

class ImportAnswer(BaseModel):
    content: str

class ImportTask(BaseModel):
    collection_name: str
    prompt: str
    completed: bool = False
    rubrics: List[ImportRubric] = []
    answers: List[str] = []
    tree: Optional[ImportTree] = None

class BatchImportRequest(BaseModel):
    tasks: List[ImportTask]

class BatchImportResponse(BaseModel):
    success: bool
    message: str
    task_count: int = 0
    rubric_count: int = 0
    answer_count: int = 0

# 历史记录模型
class ImportHistory(BaseModel):
    id: int
    task_set_id: int
    imported_by: Optional[int] = None
    import_batch_id: str
    import_type: str
    created_at: datetime

    class Config:
        from_attributes = True

class RubricHistory(BaseModel):
    id: int
    rubric_id: int
    task_id: int
    content: str
    selected: bool
    version: int
    change_type: str
    created_at: datetime

    class Config:
        from_attributes = True

class TaskHistory(BaseModel):
    id: int
    task_id: int
    query: str
    completed: bool
    change_type: str
    created_at: datetime

    class Config:
        from_attributes = True

# Diff对比模型
class RubricDiff(BaseModel):
    criterion: str
    old_point: Optional[int] = None
    new_point: Optional[int] = None
    old_selected: Optional[bool] = None
    new_selected: Optional[bool] = None
    old_axis: Optional[str] = None
    new_axis: Optional[str] = None
    change_type: str  # 'added', 'removed', 'modified'

class TaskDiff(BaseModel):
    prompt: str
    changes: List[RubricDiff]
    answers_changed: bool = False


# Tree 节点选择更新模型
class TreeNodeSelectionUpdate(BaseModel):
    selected: bool

# Tree 节点专业性更新模型
class TreeNodeProfessionalUpdate(BaseModel):
    professional: bool

# Tree 节点必答更新模型
class TreeNodeRequiredUpdate(BaseModel):
    required: bool
