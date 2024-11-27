from ninja import Schema
from typing import List, Optional


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

class UserProgressSchema(Schema):
    lesson_id: int
    quiz_score: float
    assignment_completed: bool
    assignment_score: float