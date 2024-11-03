from ninja_extra import Router

from openai import OpenAI
from decouple import config

from .schemas import LessonCreateSchema, LessonUpdateSchema, LessonDetailSchema
from module.schemas import ModuleDetailSchema
from learn_how_to_code.schemas import MessageSchema

from .models import Lesson
from module.models import Module

import helpers
import json

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
    

@router.delete("lessons/{lesson_id}", response={200: MessageSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def delete_lesson(request, lesson_id: int):
    """Deletes a specific lesson from a module."""   

    try:
        lesson = Lesson.objects.get(id=lesson_id)
        lesson.delete()

        return 200, {"message": "Lesson deleted successfully."}
    except Lesson.DoesNotExist:
        return 404, {"message": f"Lesson with id {lesson_id} not found."}
    except Exception as e:
        return 500, {"message": "An unexpected error occurred while deleting the lesson."}
    

@router.post("/modules/{module_id}/lessons/generate", response={201: ModuleDetailSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def generate_lessons(request, module_id: int):
    """Creates a new lesson within a specific module."""

    try:
        module = Module.objects.get(id=module_id)

        lessons_data = generate_lessons_for_module(module.name)

        while not lessons_data[0]['name']:
            lessons_data = generate_lessons_for_module(module.name)

        for index, lesson_data in enumerate(lessons_data):
            Lesson.objects.create(
                module=module,
                name=lesson_data["name"],
                order=Lesson.get_next_order(module_id)
            )

        return 201, module.to_dict()
    except Module.DoesNotExist:
        return 404, {"message": f"Module with id {module_id} not found."}
    except Exception as e:
        traceback.print_exc()
        return 500, {"message": "An unexpected error occurred during lesson creation."}
    

def generate_lessons_for_module(module_name: str, language: str = "polish") -> list[dict]:
    client = OpenAI(api_key=config('OPENAI_API_KEY', cast=str))

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are a lesson generator. Always respond in JSON format as a list of objects with 'name' field in {language}."},
                {"role": "user", "content": f"Generate a list of 3 unique lesson names for a module titled '{module_name}'."}
            ]
        )

        result = response.choices[0].message.content
        logger.info(f"OpenAI response for lesson generation: {result}")

        try:
            parsed_result = json.loads(result)
            return parsed_result
        except json.JSONDecodeError as e:
            return [{"error": "Model did not return valid JSON format", "response": result}]
    except Exception as e:
        raise