from ninja import Query
from ninja_extra import Router

from openai import OpenAI
from decouple import config

from lesson_content.models import LessonAssignment, LessonIntroduction, LessonQuiz, QuizOption

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

# @router.post("/modules/{module_id}/lessons", response={201: LessonDetailSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
# def create_lesson(request, payload: LessonCreateSchema, module_id: int):
#     """Creates a new lesson within a specific module."""

#     try:
#         module = Module.objects.get(id=module_id)

#         lesson_data = payload.dict()
#         lesson_data['module'] = module
#         lesson_data['order'] = Lesson.get_next_order(module_id)
#         lesson = Lesson.objects.create(**lesson_data)

#         return 201, lesson.to_dict()
#     except Module.DoesNotExist:
#         return 404, {"message": f"Module with id {module_id} not found."}
#     except Exception as e:
#         return 500, {"message": "An unexpected error occurred during lesson creation."}
    

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
        traceback.print_exc()
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

        try:
            parsed_result = json.loads(result)
            return parsed_result
        except json.JSONDecodeError as e:
            return [{"error": "Model did not return valid JSON format", "response": result}]
    except Exception as e:
        raise


@router.post("/modules/{module_id}/lessons", response={201: list[LessonDetailSchema], 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def add_lessons_with_content(
    request,
    payload: list[LessonCreateSchema],
    module_id: int,
    generate: bool = Query(False)
):
    """
    Adds lessons to a specific module. Optionally generates content for each lesson if 'generate=true'.
    """
    try:
        # Pobranie modułu
        module = Module.objects.get(id=module_id)

        # ???
        module.lessons.all().delete()
        created_lessons = []

        for lesson_data in payload:
            # Tworzenie lekcji
            lesson_dict = lesson_data.dict()
            lesson_dict['module'] = module
            lesson_dict['order'] = Lesson.get_next_order(module_id)

            lesson = Lesson.objects.create(**lesson_dict)

            if generate:
                # Generowanie pełnej zawartości lekcji
                try:
                    generated_content = generate_full_lesson_content(
                        lesson_name=lesson.topic,
                        module_name=module.name,
                        course_name=module.course.name,
                        course_description=module.course.description,
                    )

                    # Zapis opisu
                    if "description" in generated_content:
                        LessonIntroduction.objects.create(
                            lesson=lesson,
                            introduction=generated_content["description"]
                        )

                    # Zapis quizu
                    if "quiz" in generated_content:
                        for question_data in generated_content["quiz"]:
                            quiz = LessonQuiz.objects.create(
                                lesson=lesson,
                                question=question_data["question"]
                            )
                            correct_answer = question_data["answer"]
                            for option_text in question_data["options"]:
                                option = QuizOption.objects.create(
                                    quiz=quiz,
                                    answer=option_text,
                                    is_correct=(option_text == correct_answer)
                                )
                                print("Zapisana opcja:", option.to_dict())  # Debugowanie

                    # Zapis zadania
                    if "assignment" in generated_content:
                        assignment = LessonAssignment.objects.create(
                            lesson=lesson,
                            instructions=generated_content["assignment"]
                        )
                        print("Zapisane zadanie:", assignment.to_dict())  # Debugowanie
                except Exception as e:
                    traceback.print_exc()
                    return 500, {"message": f"Error while generating lesson content: {str(e)}"}

            created_lessons.append(lesson.to_dict())

        return 201, created_lessons
    except Module.DoesNotExist:
        return 404, {"message": f"Module with id {module_id} not found."}
    except Exception as e:
        traceback.print_exc()
        return 500, {"message": "An unexpected error occurred while adding lessons."}



def generate_full_lesson_content(
    lesson_name: str,
    module_name: str,
    course_name: str,
    course_description: str,
    language: str = "polish"
) -> dict:
    """
    Generates the full content for a lesson, including description, quiz, and assignment.
    """
    client = OpenAI(api_key=config('OPENAI_API_KEY', cast=str))

    try:
        # Generowanie zawartości lekcji
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a professional educational content generator in language {language}. Respond in JSON format with three keys: "
                        "'description', 'quiz', and 'assignment'. Ensure the response is a valid JSON object with:\n"
                        "- 'description': Detailed HTML content with proper tags.\n"
                        "- 'quiz': A list of 3 questions, each with 'question', 'options' (4), and the correct 'answer'.\n"
                        "- 'assignment': HTML instructions in an ordered list (<ol>)."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Generate content for a lesson titled '{lesson_name}' in the module '{module_name}', "
                        f"which is part of the course '{course_name}' described as: '{course_description}'. "
                        f"The response should be a JSON object containing the keys 'description', 'quiz', and 'assignment'."
                    )
                }
            ],
            max_tokens=1000,
            temperature=0.7
        )

        # Debugowanie odpowiedzi
        content = response.choices[0].message.content.strip()
        print("Raw OpenAI response content:", content)

        # Sprawdzanie pustej odpowiedzi
        if not content:
            raise Exception("OpenAI returned an empty response.")

        # Próba sparsowania JSON
        try:
            result = json.loads(content)
            # Walidacja kluczy odpowiedzi
            if not all(key in result for key in ["description", "quiz", "assignment"]):
                raise ValueError("Response is missing required keys: 'description', 'quiz', or 'assignment'")
            return result
        except json.JSONDecodeError:
            raise Exception(f"Failed to decode JSON: {content}")
        except ValueError as ve:
            raise Exception(f"Invalid JSON structure: {str(ve)}")

    except Exception as e:
        traceback.print_exc()
        raise Exception(f"Error during content generation: {str(e)}")
