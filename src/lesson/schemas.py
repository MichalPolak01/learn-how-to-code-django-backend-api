from ninja import Schema
from pydantic import EmailStr, Field, field_validator, BaseModel
from typing import List, Optional
import re

from lesson_content.schemas import LessonAssignmentSchema, LessonIntroductionSchema, LessonQuizDetailSchema

class LessonCreateSchema(Schema):
    topic: str

class LessonResponseSchema(BaseModel):
    modules: List[LessonCreateSchema]

class LessonUpdateSchema(Schema):
    id: Optional[int] = None
    topic: Optional[str] = None
    order: Optional[int] = None
    introduction: Optional[LessonIntroductionSchema] = None
    quiz: List[LessonQuizDetailSchema] = []
    assignment: Optional[LessonAssignmentSchema] = None


class LessonDetailSchema(Schema):
    id: int
    topic: str
    order: int
    introduction: Optional[LessonIntroductionSchema] = None
    quiz: List[LessonQuizDetailSchema]
    assignment: Optional[LessonAssignmentSchema] = None