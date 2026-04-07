from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class UserRegister(BaseModel):
    phone: str
    password: str

class UserLogin(BaseModel):
    phone: str
    password: str

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

class RubricUpdateContent(BaseModel):
    content: str
