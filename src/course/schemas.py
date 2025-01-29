from ninja import Schema
from pydantic import EmailStr, Field, field_validator
from typing import Optional, List
import re

from module.schemas import ModuleDetailSchema, ModuleUpdateSchema

from authentication.schemas import UserDetailSchema


class CourseDetailSchema(Schema):
    id: int
    name: str
    description: str
    image: str
    author: UserDetailSchema
    last_updated: str
    is_public: bool
    rating: float
    student_count: int
    lesson_count: int
    modules: List[ModuleDetailSchema]
    creator_state: str


class CoursePreviewSchema(Schema):
    id: int
    name: str
    image: str
    description: str
    author: UserDetailSchema
    last_updated: str
    is_public: bool
    rating: float
    student_count: int
    lesson_count: int


class CourseCreateSchema(Schema):
    name: str
    image: str
    description: Optional[str] = ""
    is_public: Optional[bool] = False
    creator_state: str


class CourseDeatilUpdateSchema(Schema):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    creator_state: Optional[str] = None
    image: Optional[str] = None


class RatingSchema(Schema):
    score: int


class CourseUpdateSchema(CourseCreateSchema):
    id: int
    modules: List[ModuleUpdateSchema] = []


class StatsSchema(Schema):
    courses_count: int
    students_count: int
    completed_lessons: int


class GeneralProgressStatsSchema(Schema):
    username: str
    completed_lessons: int
    started_assignments: int
    started_quizzes: int
    assignment_score_percentage: float
    quiz_score_percentage: float
    lesson_count: int


class EnrolledCourseProgressSchema(Schema):
    course_id: int
    course_name: str
    users_progress: List[GeneralProgressStatsSchema]


class LessonProgressStatsSchema(Schema):
    lesson_id: int
    lesson_topic: str
    completed_lessons: int
    assignment_score_percentage: float
    quiz_score_percentage: float
    lesson_count: int


class CourseProgressSchema(Schema):
    course_id: int
    course_name: str
    lesson_progress: List[LessonProgressStatsSchema]