from ninja import Schema
from typing import List, Optional
from pydantic import EmailStr, Field, field_validator, BaseModel


class LessonIntroductionSchema(Schema):
    id: Optional[int] = None
    description: str

class QuizOptionSchema(Schema):
    id: Optional[int] = None
    answer: str
    is_correct: bool

class LessonQuizSchema(Schema):
    question: str
    answers: List[QuizOptionSchema]

class LessonQuizDetailSchema(Schema):
    id: Optional[int] = None
    question: str
    answers: List[QuizOptionSchema]

class LessonAssignmentSchema(Schema):
    id: Optional[int] = None
    instructions: str



class LessonIntroductionResponseSchema(BaseModel):
    description: str


class QuizOptionResponseSchema(BaseModel):
    answer: str
    is_correct: bool


class LessonQuizResponseSchema(BaseModel):
    question: str
    answers: List[QuizOptionResponseSchema]


class LessonAssignmentResponseSchema(BaseModel):
    instructions: str


class LessonContentSchema(BaseModel):
    description: str
    quiz: List[LessonQuizResponseSchema]
    assignment: str

    class Config:
        schema_extra = {
            "required": ["description", "quiz", "assignment"],
        }

class UserProgressSchema(Schema):
    lesson_id: int
    quiz_score: float
    assignment_completed: bool
    assignment_score: float


class CodeEvaluationRequestSchema(BaseModel):
    lesson_id: int
    user_code: str


class CodeEvaluationResponseSchema(BaseModel):
    assignment_score: float
    message: str