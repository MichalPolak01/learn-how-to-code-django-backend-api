import json
import traceback
from ninja import Query
from ninja_extra import Router
from openai import OpenAI
from decouple import config

from lesson.models import Lesson

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
    """Adds or replaces modules in a specific course. Optionally generates lessons for each module if `generate=true`."""

    try:
        course = Course.objects.get(id=course_id, author=request.user)

        course.modules.all().delete()

        created_modules = []

        for module_data in payload:
            module_dict = module_data.dict()
            module_dict["course"] = course

            module = Module.objects.create(**module_dict)
            created_modules.append(module)

            if generate:
                try:
                    lessons_data = generate_lessons(course.name, course.description, module.name)

                    for index, lesson_data in enumerate(lessons_data):
                        Lesson.objects.create(
                            module=module,
                            topic=lesson_data["name"],
                            order=index + 1
                        )
                except Exception as e:
                    traceback.print_exc()
                    return 500, {"message": f"An error occurred while generating lessons: {str(e)}"}

        return 201, [module.to_dict() for module in created_modules]
    except Course.DoesNotExist:
        return 404, {"message": f"Course with id {course_id} not found for the current user."}
    except Exception as e:
        traceback.print_exc()
        return 500, {"message": "An unexpected error occurred while adding or replacing modules."}


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
    


def generate_lessons(course_name: str, course_description: str, module_name: str, language: str = "polish") -> list[dict]:
    """
    Generates a list of lessons for a module based on the course and module information.
    """

    client = OpenAI(api_key=config('OPENAI_API_KEY', cast=str))

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are an expert educational content generator. Respond only in JSON format with a list of objects. "
                        f"Each object should represent a lesson and must include only one field: 'name'. "
                        f"The 'name' field must contain a unique lesson title. Use {language} for all content."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Generate exactly 3 unique lesson titles for a module titled '{module_name}', "
                        f"which is part of the course '{course_name}'. "
                        f"The course is described as follows: {course_description}. "
                        f"Your response should be a valid JSON array of objects with this structure:\n\n"
                        f"[\n    {{ \"name\": \"Lesson Title 1\" }},\n    {{ \"name\": \"Lesson Title 2\" }},\n    {{ \"name\": \"Lesson Title 3\" }}\n]"
                    )
                }
            ]
        )
        
        result = response.choices[0].message.content.strip()

        try:
            parsed_result = json.loads(result)
            
            if isinstance(parsed_result, list) and all(isinstance(item, dict) and "name" in item for item in parsed_result):
                return parsed_result
            else:
                raise ValueError("Invalid JSON structure: Missing 'name' fields or wrong format")
        
        except json.JSONDecodeError:
            return [{"error": "Model did not return valid JSON format", "response": result}]
        except ValueError as ve:
            return [{"error": str(ve), "response": result}]

    except Exception as e:
        raise Exception(f"Error during lesson generation: {str(e)}")
