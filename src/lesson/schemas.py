from ninja import Schema
from pydantic import EmailStr, Field, field_validator
from typing import Optional
import re

class LessonCreateSchema(Schema):
    name: str


class LessonUpdateSchema(Schema):
    name: Optional[str] = None
    order: Optional[int] = None


class LessonDetailSchema(Schema):
    id: int
    name: str
    order: int