import json
import traceback
from typing import List
from ninja import Query
from ninja_extra import Router
from openai import OpenAI
from django.db import transaction
from decouple import config

from lesson.models import Lesson
from lesson.schemas import LessonCreateSchema, LessonResponseSchema
from .schemas import ModuleCreateSchema, ModuleUpdateSchema, ModuleDetailSchema
from learn_how_to_code.schemas import MessageSchema
from .models import Module
from course.models import Course

import helpers

router = Router()


@router.post("/{course_id}/modules", response={201: list[ModuleDetailSchema], 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def add_modules_with_lessons(
    request, 
    payload: list[ModuleCreateSchema], 
    course_id: int, 
    generate: bool = Query(False)
):
    """ Adds or replaces modules in a specific course. Optionally generates lessons for each module if `generate=true`."""

    try:
        course = Course.objects.get(id=course_id, author=request.user)

        with transaction.atomic():
            course.modules.all().delete()

            created_modules = []

            for module_data in payload:
                module = Module.objects.create(
                    course=course,
                    name=module_data.name,
                    order=module_data.order,
                    is_visible=True,
                )
                created_modules.append(module)

                if generate:
                    try:
                        lessons_data = generate_lessons(course.name, course.description, module.name)

                        for index, lesson_data in enumerate(lessons_data):
                            Lesson.objects.create(
                                module=module,
                                topic=lesson_data.topic,
                                order=index + 1
                            )
                    except Exception as e:
                        raise Exception(f"An error occurred while generating lessons: {str(e)}")

            return 201, [module.to_dict() for module in created_modules]

    except Course.DoesNotExist:
        return 404, {"message": f"Course with id {course_id} not found for the current user."}
    except Exception as e:
        traceback.print_exc()
        return 500, {"message": f"An unexpected error occurred: {str(e)}"}


@router.get('/{course_id}/modules', response={200: list[ModuleDetailSchema], 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def get_list_modules_for_course(request, course_id: int):
    """Retrieves all modules for a specific course."""

    try:
        course = Course.objects.get(id=course_id)
        modules = course.modules.all()

        return 200, [ModuleDetailSchema(**module.to_dict()) for module in modules]
    except Course.DoesNotExist:
        return 404, {"message": f"Course with id {course_id} not found for the current user."}
    except Exception as e:
        return 500, {"message": "An unexpected error occurred while retrieving list of modules."}
    

@router.get('/{course_id}/modules/{module_id}', response={200: ModuleDetailSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def get_module(request, course_id: int, module_id: int):
    """Retrieves details of a specific module."""

    try:
        module = Module.objects.get(id=module_id, course=course_id)

        return 200, module.to_dict()
    except Module.DoesNotExist:
        return 404, {"message": f"Module with id {module_id} not found."}
    except Exception as e:
        return 500, {"message": "An unexpected error occurred while retrieving the module."}
    

@router.patch('/{course_id}/modules/{module_id}', response={200: ModuleDetailSchema, 400: MessageSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def update_module(request, payload: ModuleUpdateSchema, course_id: int, module_id: int):
    """Updates details of a specific module."""

    try:
        module = Module.objects.get(id=module_id, course=course_id)
        
        for attr, value in payload.dict(exclude_unset=True).items():
            setattr(module, attr, value)

        module.save()

        return 200, module.to_dict()
    except Module.DoesNotExist:
        return 404, {"message": f"Module with id {module_id} not found."}
    except Exception as e:
        return 500, {"message": "An unexpected error occurred while updating the module."}
    

@router.delete('/{course_id}/modules/{module_id}', response={200: MessageSchema, 400: MessageSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def delete_module(request, course_id: int, module_id: int):
    """Deletes a specific module from a course."""   

    try:
        module = Module.objects.get(id=module_id, course=course_id)
        module.delete()

        return 200, {"message": "Module deleted successfully."}
    except Module.DoesNotExist:
        return 404, {"message": f"Module with id {module_id} not found."}
    except Exception as e:
        return 500, {"message": "An unexpected error occurred while deleting the module."}
    

def generate_lessons(course_name: str, course_description: str, module_name: str, language: str = "polish") -> List[LessonCreateSchema]:
    """Generates a list of lessons for a module based on the course and module information."""
    client = OpenAI(api_key=config('OPENAI_API_KEY', cast=str))

    try:
        completion = client.beta.chat.completions.parse(
            model=config('OPEN_API_MODEL', cast=str),
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are an educational content generator. Generate lesson topics in JSON format as a list of objects. "
                        f"Language: {language}."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Generate exactly 3 unique lesson topics for a module titled '{module_name}', "
                        f"which is part of the course titled '{course_name}'. "
                        f"The course is described as follows: {course_description}."
                    )
                }
            ],
            response_format=LessonResponseSchema,
        )

        parsed_response = completion.choices[0].message.parsed

        return parsed_response.modules

    except Exception as e:
        raise Exception(f"An error occurred while generating lessons: {str(e)}")