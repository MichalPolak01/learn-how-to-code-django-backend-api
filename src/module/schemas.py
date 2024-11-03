from ninja import Schema
from pydantic import EmailStr, Field, field_validator
from typing import Optional
import re

class ModuleCreateSchema(Schema):
    name: str
    is_visible: Optional[bool] = True


class ModuleUpdateSchema(Schema):
    name: Optional[str] = None
    order: Optional[int] = None
    is_visible: Optional[bool] = None


class ModuleDetailSchema(Schema):
    id: int
    name: str
    order: int
    is_visible: bool
    lesson_count: int