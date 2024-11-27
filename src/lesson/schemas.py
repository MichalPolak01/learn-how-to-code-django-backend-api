from ninja import Schema
from pydantic import EmailStr, Field, field_validator
from typing import List, Optional
import re

from lesson_content.schemas import LessonAssignmentSchema, LessonIntroductionSchema, LessonQuizDetailSchema

class LessonCreateSchema(Schema):
    topic: str


class LessonUpdateSchema(Schema):
    topic: Optional[str] = None
    order: Optional[int] = None


class LessonDetailSchema(Schema):
    id: int
    topic: str
    order: int
    introduction: Optional[LessonIntroductionSchema] = None
    quiz: List[LessonQuizDetailSchema]
    assignment: Optional[LessonAssignmentSchema] = None