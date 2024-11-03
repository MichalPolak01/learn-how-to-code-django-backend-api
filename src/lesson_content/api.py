from ninja_extra import Router

from openai import OpenAI
from decouple import config

from .schemas import LessonDescriptionSchema, LessonQuizSchema, LessonAssignmentSchema
from module.schemas import ModuleDetailSchema
from learn_how_to_code.schemas import MessageSchema

from .models import LessonDescription
from lesson.models import Lesson

import helpers
import json

import logging
import traceback
logger = logging.getLogger(__name__)

router = Router()

@router.post('/lessons/{lesson_id}/description/generate', response={201: LessonDescriptionSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def generate_lesson_description(request, lesson_id: int):
    """Generates a description for a specific lesson."""

    try:
        lesson = Lesson.objects.get(id=lesson_id)

        description = generate_description(lesson.name)

        lesson_description = LessonDescription.objects.create(
            lesson=lesson,
            description=description
        )
        
        return 201, lesson_description
    except Lesson.DoesNotExist:
        return 404, {"message": f"Lesson with id {lesson_id} not found."}
    except Exception as e:
        traceback.print_exc()
        return 500, {"message": "An error occurred while generating the description."}
    

@router.post('/lessons/{lesson_id}/description', response={201: LessonDescriptionSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def generate_lesson_description(request, payload: LessonDescriptionSchema, lesson_id: int):
    """Allows a teacher to manually create a description for a lesson."""

    try:
        lesson = Lesson.objects.get(id=lesson_id)

        lesson_description = LessonDescription.objects.create(
            lesson=lesson,
            description=payload.description
        )
        
        return 201, lesson_description
    except Lesson.DoesNotExist:
        return 404, {"message": f"Lesson with id {lesson_id} not found."}
    except Exception as e:
        return 500, {"message": "An error occurred while creating the description."}
    

def generate_description(lesson_name: str, language: str = "polish"):
    client = OpenAI(api_key=config('OPENAI_API_KEY', cast=str))
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"You are a lesson description generator. Respond in {language}."},
            {"role": "user", "content": f"Provide a detailed description for a lesson on {lesson_name}."}
            # {"role": "user", "content": f"Provide a short description for a lesson on {lesson_name}."}
        ]
    )
    return response.choices[0].message.content