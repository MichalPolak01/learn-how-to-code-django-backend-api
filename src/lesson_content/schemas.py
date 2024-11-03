from ninja import Schema
from typing import List


class LessonDescriptionSchema(Schema):
    description: str

class QuizOptionSchema(Schema):
    option: str
    is_correct: bool

class LessonQuizSchema(Schema):
    question: str
    options: List[QuizOptionSchema]

class LessonAssignmentSchema(Schema):
    instruction: str

class UserProgressSchema(Schema):
    lesson_id: int
    quiz_score: float
    assignment_completed: bool
    assignment_score: float