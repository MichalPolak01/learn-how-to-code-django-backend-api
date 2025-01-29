from django.shortcuts import get_object_or_404
from ninja import Query
from ninja_extra import Router
from django.db import transaction
import traceback

from openai import OpenAI
from decouple import config

from lesson_content.models import LessonAssignment, LessonIntroduction, LessonQuiz, QuizOption
from lesson_content.schemas import LessonContentSchema

from .schemas import LessonCreateSchema, LessonUpdateSchema, LessonDetailSchema, StudentProgressResponseSchema, StudentProgressSchema
from learn_how_to_code.schemas import MessageSchema
from .models import Lesson, StudentProgress
from module.models import Module

import helpers

router = Router()


@router.post("/modules/{module_id}/lessons", response={201: list[LessonDetailSchema], 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def add_lessons_with_content(request, payload: list[LessonCreateSchema], module_id: int, generate: bool = Query(False)):
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
    

@router.get("/lessons/{lesson_id}", response={200: LessonDetailSchema, 403: MessageSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def get_lesson(request, lesson_id: int):
    """Retrieves details of a specific lesson if the course is public or the user is the course author."""

    try:
        user = request.user

        lesson = Lesson.objects.select_related("module").get(id=lesson_id)
        course = lesson.module.course

        if not course.is_public and course.author != user:
            return 403, {"message": "You do not have permission to view this lesson."}

        return 200, lesson.to_dict()

    except Lesson.DoesNotExist:
        return 404, {"message": f"Lesson with id {lesson_id} not found."}
    except Exception as e:
        traceback.print_exc()
        return 500, {"message": "An unexpected error occurred while retrieving the lesson."}


@router.patch("/lessons/{lesson_id}", response={200: LessonDetailSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
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
    

@router.delete("/lessons/{lesson_id}", response={200: MessageSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
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


@router.post("/student-progress", response={200: MessageSchema, 201: MessageSchema, 400: MessageSchema}, auth=helpers.auth_required)
def add_or_update_student_progress(request, data: StudentProgressSchema):
    """Adds or updates student progress in lesson."""

    try:
        with transaction.atomic():
            user = request.user
            lesson = get_object_or_404(Lesson, id=data.lesson_id)

            progress, created = StudentProgress.objects.get_or_create(
                user=user,
                lesson=lesson,
                defaults={
                    "introduction_completed": data.introduction_completed or False,
                    "quiz_score": data.quiz_score,
                    "assignment_score": data.assignment_score,
                    "lesson_completed": False,
                },
            )

            if not created:
                if data.introduction_completed is not None:
                    progress.introduction_completed = progress.introduction_completed or data.introduction_completed
                if data.quiz_score is not None:
                    progress.quiz_score = max(progress.quiz_score or 0, data.quiz_score)
                if data.assignment_score is not None:
                    progress.assignment_score = max(progress.assignment_score or 0, data.assignment_score)

                if (
                    progress.introduction_completed
                    and (progress.quiz_score or 0) >= 70
                    and (progress.assignment_score or 0) >= 70
                ):
                    progress.lesson_completed = True

                    current_module = lesson.module
                    next_lesson = current_module.lessons.filter(order__gt=lesson.order).order_by('order').first()

                    if not next_lesson:
                        next_module = current_module.course.modules.filter(order__gt=current_module.order).order_by('order').first()
                        if next_module:
                            next_lesson = next_module.lessons.order_by('order').first()

                    if next_lesson:
                        StudentProgress.objects.get_or_create(
                            user=user,
                            lesson=next_lesson,
                            defaults={
                                "introduction_completed": False,
                                "quiz_score": None,
                                "assignment_score": None,
                                "lesson_completed": False,
                            },
                        )

                progress.save()

            return 201 if created else 200, {"message": "Progress added or updated successfully."}

    except Exception as e:
        return 400, {"message": f"Error: {str(e)}"}


@router.get("/student-progress/{course_id}", response={200: list[StudentProgressResponseSchema], 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def get_student_progress(request, course_id: int):
    """Retrieves progress for a student for all lessons in a given `course_id`."""

    try:
        user = request.user

        modules = Module.objects.filter(course_id=course_id)
        lessons = Lesson.objects.filter(module__in=modules)

        progress_list = StudentProgress.objects.filter(user=user, lesson__in=lessons)

        if not progress_list.exists():
            return 404, {"message": f"No progress found for user {user.id} in course {course_id}."}

        response_data = [
            StudentProgressResponseSchema(
                lesson_id=progress.lesson.id,
                student=user.to_dict(),
                introduction_completed=progress.introduction_completed,
                quiz_score=progress.quiz_score,
                assignment_score=progress.assignment_score,
                lesson_completed=progress.lesson_completed,
            )
            for progress in progress_list
        ]

        return 200, response_data

    except Exception as e:
        traceback.print_exc()
        return 500, {"message": f"An unexpected error occurred: {str(e)}"}


def generate_full_lesson_content(lesson_name: str, module_name: str, course_name: str, course_description: str, language: str = "polish") -> LessonContentSchema:
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