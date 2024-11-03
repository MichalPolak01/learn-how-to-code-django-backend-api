from ninja import Schema
from pydantic import EmailStr, Field, field_validator
from typing import Optional, List
import re

from module.schemas import ModuleDetailSchema

from authentication.schemas import UserDetailSchema


class CourseDetailSchema(Schema):
    id: int
    name: str
    description: str
    author: UserDetailSchema
    last_updated: str
    is_public: bool
    rating: float
    student_count: int
    lesson_count: int
    modules: List[ModuleDetailSchema]


class CourseCreateSchema(Schema):
    name: str
    description: Optional[str] = ""
    generate_modules: Optional[bool] = False


class CourseUpdateSchema(Schema):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None


class RatingSchema(Schema):
    score: int