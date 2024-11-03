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

@router.post("/{module_id}/lessons", response={201: LessonDetailSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
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