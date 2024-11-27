from ninja import Schema
from pydantic import EmailStr, Field, field_validator
from typing import List, Optional
import re

from lesson_content.schemas import LessonAssignmentSchema, LessonIntroductionSchema, LessonQuizDetailSchema

class LessonCreateSchema(Schema):
    name: str


class LessonUpdateSchema(Schema):
    name: Optional[str] = None
    order: Optional[int] = None


class LessonDetailSchema(Schema):
    id: int
    name: str
    order: int
    description: List[LessonIntroductionSchema]
    quizzes: List[LessonQuizDetailSchema]
    assignment: List[LessonAssignmentSchema]