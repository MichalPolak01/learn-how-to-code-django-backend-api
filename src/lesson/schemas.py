from ninja import Schema
from pydantic import EmailStr, Field, field_validator, BaseModel
from typing import List, Optional
import re

from authentication.schemas import UserDetailSchema
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



class StudentProgressSchema(BaseModel):
    lesson_id: int
    introduction_completed: Optional[bool] = None
    quiz_score: Optional[float] = None
    assignment_score: Optional[float] = None
    lesson_completed: Optional[bool] = None


class StudentProgressResponseSchema(BaseModel):
    lesson_id: int
    student: UserDetailSchema
    introduction_completed: Optional[bool] = None
    quiz_score: Optional[float] = None
    assignment_score: Optional[float] = None
    lesson_completed: Optional[bool] = None