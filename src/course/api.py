import traceback
from typing import List
from ninja import Query, Router
from django.db import transaction

from lesson.models import Lesson
from lesson_content.models import LessonAssignment, LessonIntroduction, LessonQuiz, QuizOption
from module.schemas import ModuleCreateSchema, ModuleResponseSchema

from .models import Course, Rating
from module.models import Module
from .schemas import CourseCreateSchema, CourseUpdateSchema, CourseDetailSchema, RatingSchema, CourseDeatilUpdateSchema
from learn_how_to_code.schemas import MessageSchema
import helpers

from openai import OpenAI
from decouple import config


router = Router()

    
@router.post("", response={201: CourseDetailSchema, 400: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def create_course(request, payload: CourseCreateSchema, generate: bool = Query(False)):
    """Create a new course. Optionally generates modules if param `generate=true` is provided in the URL."""
    
    try:
        author = request.user

        if author.role != "TEACHER":
            return 400, {"message": "Only teachers can create courses."}

        if Course.objects.filter(name=payload.name).exists():
            return 400, {"message": "A course with this name already exists."}

        with transaction.atomic():
            course_data = payload.dict()
            course_data['author'] = author
            course = Course.objects.create(**course_data)

            if generate:
                try:
                    modules_data = generate_modules(course.name, course.description)
                    
                    for index, module_data in enumerate(modules_data):
                        Module.objects.create(
                            course=course,
                            name=module_data.name,
                            order=index + 1,
                            is_visible=True
                        )
                except Exception as e:
                    raise Exception(f"Module generation failed: {str(e)}")

        return 201, course.to_dict()

    except Exception as e:
        traceback.print_exc()
        return 500, {"message": f"An unexpected error occurred during course creation: {str(e)}"}
    
    
@router.get('', response={200: list[CourseDetailSchema], 400: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def get_list_public_courses(request, option: str = None):
    """Retrieves a list of all public courses. Or if param is `option=my` retrieves only my course."""

    try:
        if option:
            
            if option == "my":
                courses = Course.objects.filter(is_public=True)
            else:
                return 400, {"message": "Option is not valid."}
        else:
            courses = Course.objects.filter(author=request.user)

        return 200, [CourseDetailSchema(**course.to_dict()) for course in courses]
    except Exception as e:
        return 500, {"message": "An unexpected error occurred while retrieving courses."}
    

@router.get('/{course_id}', response={200: CourseDetailSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def get_public_course(request, course_id: int):
    """Retrieves details of a specific public course by ID."""

    try:
        course = Course.objects.get(id=course_id)
        
        return 200, course.to_dict()
    except Course.DoesNotExist:
        return 404, {"message": f"No public course found with id {course_id}."}
    except Exception as e:
        traceback.print_exc()
        return 500, {"message": "An unexpected error occurred during course getting."}
       

@router.patch('/{course_id}', response={200: CourseDetailSchema, 400: MessageSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def update_my_course(request, payload: CourseDeatilUpdateSchema, course_id: int):
    """Updates details of a specific course created by the authenticated user."""

    try:
        course = Course.objects.get(id=course_id, author=request.user)

        if payload.name and Course.objects.filter(name=payload.name).exclude(id=course_id).exists():
            return 400, {"message": "This course name is already taken by another course."}
        
        for attr, value in payload.dict(exclude_unset=True).items():
            setattr(course, attr, value)

        course.save()

        return 200, course.to_dict()
    except Course.DoesNotExist:
        return 404, {"message": f"Course with id {course_id} not found for the current user."}
    except Exception as e:
        return 500, {"message": "An unexpected error occurred while updating the course."}


@router.delete('/{course_id}', response={200: MessageSchema, 400: MessageSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def delete_my_course(request, course_id: int):
    """Deletes a specific course created by the authenticated user."""   

    try:
        course = Course.objects.get(id=course_id, author=request.user)
        course.delete()

        return 200, {"message": "Course deleted successfully."}
    except Course.DoesNotExist:
        return 404, {"message": f"Course with id {course_id} not found for the current user."}
    except Exception as e:
        return 500, {"message": "An unexpected error occurred while deleting the course."}


@router.post('/{course_id}/enroll', response={200: MessageSchema, 400: MessageSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def enroll_student(request, course_id: int):
    """Enrolls the authenticated user (student) in a public course."""

    try:
        course = Course.objects.get(id=course_id, is_public=True)

        if request.user in course.students.all():
            return 400, {"message": "Already enrolled in this course."}
        
        course.students.add(request.user)

        return 200, {"message": "Successfully enrolled in the course."}
    except Course.DoesNotExist:
        return 404, {"message": f"No public course found with id {course_id}."}
    except Exception as e:
        return 500, {"message": "An unexpected error occurred during enrollment in the course."}
    

@router.post('/{course_id}/rate', response={200: MessageSchema, 400: MessageSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def rate_course(request, course_id: int, payload: RatingSchema):
    """Allows an enrolled user to rate a public course."""

    try:
        course = Course.objects.get(id=course_id, is_public=True)

        if not course.students.filter(id=request.user.id).exists():
            return 400, {"message": "Only enrolled users can rate this course."}
        
        Rating.objects.update_or_create(
            course=course, user=request.user,
            defaults={'score': payload.score}
        )

        return 200, {"message": "Course rated successfully."}
    except Course.DoesNotExist:
        return 404, {"message": f"No public course found with id {course_id}."}
    except Exception as e:
        return 500, {"message": "An unexpected error occurred during the course rating process."}
    

@router.put("/{course_id}", response={200: CourseDetailSchema, 404: MessageSchema, 400: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def update_course(request, course_id: int, payload: CourseUpdateSchema):
    """Updates an entire course."""

    try:
        course = Course.objects.get(id=course_id, author=request.user)
        course.name = payload.name
        course.description = payload.description
        course.is_public = payload.is_public
        course.creator_state = payload.creator_state
        course.save()

        course.modules.all().delete()

        for module_data in payload.modules:
            module = Module.objects.create(
                course=course,
                name=module_data.name,
                order=module_data.order,
                is_visible=module_data.is_visible,
            )

            for lesson_data in module_data.lessons:
                lesson = Lesson.objects.create(
                    module=module,
                    topic=lesson_data.topic,
                    order=lesson_data.order,
                )

                if lesson_data.introduction:
                    LessonIntroduction.objects.create(
                        lesson=lesson,
                        description=lesson_data.introduction.description,
                    )

                if lesson_data.quiz:
                    for quiz_data in lesson_data.quiz:
                        quiz = LessonQuiz.objects.create(
                            lesson=lesson,
                            question=quiz_data.question,
                        )

                        for option_data in quiz_data.answers:
                            QuizOption.objects.create(
                                question=quiz,
                                answer=option_data.answer,
                                is_correct=option_data.is_correct,
                            )

                if lesson_data.assignment:
                    LessonAssignment.objects.create(
                        lesson=lesson,
                        instructions=lesson_data.assignment.instructions,
                    )

        return 200, course.to_dict()
    except Course.DoesNotExist:
        return 404, {"message": f"Course with id {course_id} not found or unauthorized."}
    except Exception as e:
        traceback.print_exc()
        return 500, {"message": f"An error occurred: {str(e)}"}


def generate_modules(course_name: str, course_description: str, language: str = "polish") -> List[ModuleCreateSchema]:
    """Generates module for course."""

    client = OpenAI(api_key=config('OPENAI_API_KEY', cast=str))

    try:
        completion = client.beta.chat.completions.parse(
            model=config('OPEN_API_MODEL', cast=str),
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a module generator for programing course. Respond in JSON format as a list of module objects. "
                        f"Language: {language}."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Generate 3 modules for a course titled '{course_name}' with the description: {course_description}."
                    )
                }
            ],
            response_format=ModuleResponseSchema,
        )

        parsed_response = completion.choices[0].message.parsed

        return parsed_response.modules

    except Exception as e:
        raise Exception(f"An error occurred while generating modules: {str(e)}")