from ninja_extra import Router

from .schemas import LessonCreateSchema, LessonUpdateSchema, LessonDetailSchema
from learn_how_to_code.schemas import MessageSchema

from .models import Lesson
from module.models import Module

import helpers

import logging
import traceback
logger = logging.getLogger(__name__)

router = Router()

@router.post("/modules/{module_id}/lessons", response={201: LessonDetailSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def create_lesson(request, payload: LessonCreateSchema, module_id: int):
    """Creates a new lesson within a specific module."""

    try:
        module = Module.objects.get(id=module_id)

        lesson_data = payload.dict()
        lesson_data['module'] = module
        lesson_data['order'] = Lesson.get_next_order(module_id)
        lesson = Lesson.objects.create(**lesson_data)

        return 201, lesson.to_dict()
    except Module.DoesNotExist:
        return 404, {"message": f"Module with id {module_id} not found."}
    except Exception as e:
        return 500, {"message": "An unexpected error occurred during lesson creation."}
    

@router.get("/modules/{module_id}/lessons", response={200: list[LessonDetailSchema], 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def get_list_lessons_for_module(request, module_id: int):
    """Retrieves all lessons for a specific module."""

    try:
        module = Module.objects.get(id=module_id)
        lessons = module.lessons.all()

        return 200, [LessonDetailSchema(**lesson.to_dict()) for lesson in lessons]
    except Module.DoesNotExist:
        return 404, {"message": f"Module with id {module_id} not found."}
    except Exception as e:
        return 500, {"message": "An unexpected error occurred while retrieving list of lessons."}
    

@router.get("lessons/{lesson_id}", response={200: LessonDetailSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def get_lesson(request, lesson_id: int):
    """Retrieves details of a specific lesson."""

    try:
        lesson = Lesson.objects.get(id=lesson_id)

        return 200, lesson.to_dict()
    except Lesson.DoesNotExist:
        return 404, {"message": f"Lesson with id {lesson_id} not found."}
    except Exception as e:
        return 500, {"message": "An unexpected error occurred while retrieving the lesson."}
    

@router.patch("lessons/{lesson_id}", response={200: LessonDetailSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def update_lesson(request, payload: LessonUpdateSchema, lesson_id: int):
    """Update details of a specific lesson."""

    try:
        lesson = Lesson.objects.get(id=lesson_id)

        for attr, value in payload.dict(exclude_unset=True).items():
            setattr(lesson, attr, value)

        lesson.save()

        return 200, lesson.to_dict()
    except Lesson.DoesNotExist:
        return 404, {"message": f"Lesson with id {lesson_id} not found."}
    except Exception as e:
        return 500, {"message": "An unexpected error occurred while updating the lesson."}