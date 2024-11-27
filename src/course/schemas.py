from ninja import Schema
from pydantic import EmailStr, Field, field_validator
from typing import Optional, List
import re

from module.schemas import ModuleDetailSchema

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
    modules: List[ModuleDetailSchema]
    creator_state: str


class CourseCreateSchema(Schema):
    name: str
    description: Optional[str] = ""
    is_public: Optional[bool] = False
    creator_state: str


class CourseDeatilUpdateSchema(Schema):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    creator_state: Optional[str] = None


class RatingSchema(Schema):
    score: int





# UPDATE

from pydantic import BaseModel
from typing import List, Optional

class CourseAuthorSchema(BaseModel):
    id: int
    username: str
    email: str
    role: str


class QuizOptionSchema(BaseModel):
    id: Optional[int] = None
    option: str
    is_correct: bool

class LessonQuizSchema(BaseModel):
    id: Optional[int] = None
    question: str
    options: List[QuizOptionSchema]

class LessonDescriptionSchema(BaseModel):
    id: Optional[int] = None
    introduction: str

class LessonAssignmentSchema(BaseModel):
    id: Optional[int] = None
    instructions: str

class LessonUpdateSchema(BaseModel):
    id: Optional[int] = None  # Id nie jest wymagane dla nowych lekcji
    name: str
    order: int
    # description: List[LessonDescriptionSchema] = []
    description: Optional[LessonDescriptionSchema] = None  # Zmienione na obiekt
    quizzes: List[LessonQuizSchema] = []
    assignment: List[LessonAssignmentSchema] = []

class ModuleUpdateSchema(BaseModel):
    id: Optional[int] = None  # Id nie jest wymagane dla nowych modułów
    name: str
    order: int
    is_visible: bool
    lessons: List[LessonUpdateSchema] = []

class CourseUpdateSchema(BaseModel):
    id: int  # Id kursu jest wymagane
    creator_state: Optional[str] = None
    name: str
    description: str
    is_public: bool
    modules: List[ModuleUpdateSchema] = []
