from ninja import Schema
from pydantic import BaseModel
from typing import Optional, List

from lesson.schemas import LessonDetailSchema, LessonUpdateSchema


class ModuleCreateSchema(Schema):
    name: str
    order: int


class ModuleResponseSchema(BaseModel):
    modules: List[ModuleCreateSchema]


class ModuleUpdateSchema(Schema):
    id: Optional[int] = None 
    name: Optional[str] = None
    order: Optional[int] = None
    is_visible: Optional[bool] = None
    lessons: List[LessonUpdateSchema] = []


class ModuleDetailSchema(Schema):
    id: int
    name: str
    order: int
    is_visible: bool
    lesson_count: int
    lessons: List[LessonDetailSchema]