from ninja import Query
from ninja_extra import Router
from django.db import transaction

from openai import OpenAI
from decouple import config

from lesson_content.models import LessonAssignment, LessonIntroduction, LessonQuiz, QuizOption
from lesson_content.schemas import LessonContentSchema

from .schemas import LessonCreateSchema, LessonUpdateSchema, LessonDetailSchema
from learn_how_to_code.schemas import MessageSchema

from .models import Lesson
from module.models import Module

import helpers

import logging
import traceback
logger = logging.getLogger(__name__)

router = Router()


@router.post("/modules/{module_id}/lessons", response={201: list[LessonDetailSchema], 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def add_lessons_with_content(
    request,
    payload: list[LessonCreateSchema],
    module_id: int,
    generate: bool = Query(False)
):
    """Adds lessons to a specific module. Optionally generates content for each lesson if param `generate=true`."""
    try:
        module = Module.objects.get(id=module_id)

        with transaction.atomic():
            module.lessons.all().delete()
            created_lessons = []

            for lesson_data in payload:
                lesson_dict = lesson_data.dict()
                lesson_dict['module'] = module
                lesson_dict['order'] = Lesson.get_next_order(module_id)

                lesson = Lesson.objects.create(**lesson_dict)

                if generate:
                    try:
                        generated_content = generate_full_lesson_content(
                            lesson_name=lesson.topic,
                            module_name=module.name,
                            course_name=module.course.name,
                            course_description=module.course.description,
                        )

                        print(generated_content)

                        LessonIntroduction.objects.create(
                            lesson=lesson,
                            description=generated_content.description
                        )

                        for question_data in generated_content.quiz:
                            quiz = LessonQuiz.objects.create(
                                lesson=lesson,
                                question=question_data.question
                            )
                            for option_data in question_data.answers:
                                QuizOption.objects.create(
                                    question=quiz,
                                    answer=option_data.answer,
                                    is_correct=option_data.is_correct
                                )

                        LessonAssignment.objects.create(
                            lesson=lesson,
                            instructions=generated_content.assignment
                        )

                    except Exception as e:
                        raise Exception(f"Error while generating lesson content: {str(e)}")

                created_lessons.append(lesson.to_dict())

        return 201, created_lessons

    except Module.DoesNotExist:
        return 404, {"message": f"Module with id {module_id} not found."}
    except Exception as e:
        traceback.print_exc()
        return 500, {"message": "An unexpected error occurred while adding lessons."}


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
        traceback.print_exc()
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


def generate_full_lesson_content(
    lesson_name: str,
    module_name: str,
    course_name: str,
    course_description: str,
    language: str = "polish"
) -> LessonContentSchema:
    """Generates the full content for a lesson, including description, quiz, and assignment."""
    client = OpenAI(api_key=config('OPENAI_API_KEY', cast=str))

    try:
        completion = client.beta.chat.completions.parse(
            model=config('OPEN_API_MODEL', cast=str),
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a professional educational content generator in language {language}. "
                        "Create detailed content for a programming lesson. Respond in JSON format as a single object "
                        "with keys 'description', 'quiz', and 'assignment'.\n\n"
                        "- 'description': A detailed HTML-formatted explanation of the topic, including examples.\n"
                        "- 'quiz': A list of 3 single-choice questions directly based on the lesson topic and description.\n"
                        "- 'assignment': A clear and simple task description that does not include any sample or pre-filled code. "
                        "Only provide task instructions for the student to implement on their own."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Generate detailed content for a lesson titled '{lesson_name}' in the module '{module_name}', "
                        f"which is part of the course '{course_name}' described as: '{course_description}'."
                    )
                }
            ],
            response_format=LessonContentSchema,
        )

        return completion.choices[0].message.parsed

    except Exception as e:
        raise Exception(f"Error during content generation: {str(e)}")

