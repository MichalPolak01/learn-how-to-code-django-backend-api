from ninja import Schema
from pydantic import EmailStr, Field, field_validator
from typing import Optional
import re

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


class CourseCreateSchema(Schema):
    name: str
    description: str


class RatingSchemaResponse(Schema):
    score: int
