from ninja import Schema
from pydantic import EmailStr, Field, field_validator
from typing import Optional, List
import re

from module.schemas import ModuleDetailSchema, ModuleUpdateSchema

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
    creator_state: str


class CoursePreviewSchema(Schema):
    id: int
    name: str
    description: str
    author: UserDetailSchema
    last_updated: str
    is_public: bool
    rating: float
    student_count: int
    lesson_count: int


class CourseCreateSchema(Schema):
    name: str
    description: Optional[str] = ""
    is_public: Optional[bool] = False
    creator_state: str


class CourseDeatilUpdateSchema(Schema):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    creator_state: Optional[str] = None


class RatingSchema(Schema):
    score: int

class CourseUpdateSchema(CourseCreateSchema):
    id: int
    modules: List[ModuleUpdateSchema] = []
