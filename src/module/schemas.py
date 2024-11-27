from ninja import Schema
from pydantic import EmailStr, Field, field_validator
from typing import Optional, List
import re

from lesson.schemas import LessonDetailSchema, LessonUpdateSchema

class ModuleCreateSchema(Schema):
    name: str
    order: int
    is_visible: Optional[bool] = True


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