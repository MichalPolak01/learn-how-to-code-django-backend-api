import traceback
from ninja import Query, Router

from lesson.models import Lesson
from lesson_content.models import LessonAssignment, LessonIntroduction, LessonQuiz, QuizOption

from .models import Course, Rating
from module.models import Module
from .schemas import CourseCreateSchema, CourseUpdateSchema, CourseDetailSchema, RatingSchema, CourseDeatilUpdateSchema
from learn_how_to_code.schemas import MessageSchema
import helpers
import json

from openai import OpenAI
from decouple import config


router = Router()

@router.post("", response={201: CourseDetailSchema, 400: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def create_course(request, payload: CourseCreateSchema, generate: bool = Query(False)):
    """Endpoint to create a new course. Optionally generates modules if 'generate=true' is provided in the URL."""

    try:
        author = request.user

        if author.role != "TEACHER":
            return 400, {"message": "Only teachers can create courses."}

        if Course.objects.filter(name=payload.name).exists():
            return 400, {"message": "A course with this name already exists."}

        course_data = payload.dict()
        course_data['author'] = author

        course = Course.objects.create(**course_data)

        if generate:
            try:
                modules_data = generate_modules(course.name, course.description)
                for index, module_data in enumerate(modules_data):
                    Module.objects.create(
                        course=course,
                        name=module_data["name"],
                        order=index + 1,
                        is_visible=True
                    )
            except Exception as e:
                return 500, {"message": f"An error occurred during module generation: {str(e)}"}

        return 201, course.to_dict()
    except Exception as e:
        traceback.print_exc()
        return 500, {"message": "An unexpected error occurred during course creation."}
    
    
@router.get('', response={200: list[CourseDetailSchema], 500: MessageSchema}, auth=helpers.auth_required)
def get_list_public_courses(request):
    """Retrieves a list of all public courses."""

    try:
        courses = Course.objects.filter(is_public=True)

        return 200, [CourseDetailSchema(**course.to_dict()) for course in courses]
    except Exception as e:
        return 500, {"message": "An unexpected error occurred while retrieving courses."}
    

@router.get('/my', response={200: list[CourseDetailSchema], 500: MessageSchema}, auth=helpers.auth_required)
def get_list_my_courses(request):
    """Retrieves a list of courses created by the authenticated user (teacher)."""

    try:
        courses = Course.objects.filter(author=request.user)

        return 200, [CourseDetailSchema(**course.to_dict()) for course in courses]
    except Exception as e:
        return 500, {"message": "An unexpected error occurred while retrieving your courses."}
    

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
    

@router.get('/my/{course_id}', response={200: CourseDetailSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def get_my_course(request, course_id: int):
    """Retrieves details of a specific course created by the authenticated user (teacher)."""

    try:
        course = Course.objects.get(id=course_id, author=request.user)
        
        return 200, course.to_dict()
    except Course.DoesNotExist:
        return 404, {"message": f"Course with id {course_id} not found for the current user."}
    except Exception as e:
        return 500, {"message": "An unexpected error occurred while retrieving the course."}
    

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
    


def generate_modules(course_name: str, course_description: str, language: str = "polish") -> list[dict]:
    client = OpenAI(api_key=config('OPENAI_API_KEY', cast=str))

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are a module generator. Always respond in JSON format as a list of objects with 'name' field in {language}."},
                {"role": "user", "content": f"Generate a list of 3 modules for a course titled '{course_name}' with the following description: {course_description}. Each module should be an object with a 'name' field."}
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





@router.put("/{course_id}", response={200: CourseDetailSchema, 404: MessageSchema, 400: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def update_course(request, course_id: int, payload: CourseUpdateSchema):
    """
    Updates an entire course, including its modules, lessons, and their content.
    """
    try:
        # Pobierz kurs i weryfikacja autora
        course = Course.objects.get(id=course_id, author=request.user)
        course.name = payload.name
        course.description = payload.description
        course.is_public = payload.is_public
        course.save()

        # Obsługa modułów
        existing_module_ids = {module.id for module in course.modules.all()}
        incoming_module_ids = {module.id for module in payload.modules if module.id is not None}

        Module.objects.filter(id__in=existing_module_ids - incoming_module_ids).delete()

        for module_data in payload.modules:
            # Obsługa istniejących lub nowych modułów
            if module_data.id:
                module = Module.objects.get(id=module_data.id, course=course)
                module.name = module_data.name
                module.order = module_data.order
                module.is_visible = module_data.is_visible
                module.save()
            else:
                module = Module.objects.create(
                    course=course,
                    name=module_data.name,
                    order=module_data.order,
                    is_visible=module_data.is_visible,
                )

            # Obsługa lekcji
            existing_lesson_ids = {lesson.id for lesson in module.lessons.all()}
            incoming_lesson_ids = {lesson.id for lesson in module_data.lessons if lesson.id is not None}

            Lesson.objects.filter(id__in=existing_lesson_ids - incoming_lesson_ids).delete()

            for lesson_data in module_data.lessons:
                # Obsługa istniejących lub nowych lekcji
                if lesson_data.id:
                    lesson = Lesson.objects.get(id=lesson_data.id, module=module)
                    lesson.topic = lesson_data.topic
                    lesson.order = lesson_data.order
                    lesson.save()
                else:
                    lesson = Lesson.objects.create(
                        module=module,
                        name=lesson_data.name,
                        order=lesson_data.order,
                    )

                # Opis lekcji
                # Obsługa opisu lekcji
                if lesson_data.description:
                    desc_data = lesson_data.description
                    LessonIntroduction.objects.update_or_create(
                        lesson=lesson,
                        defaults={"description": desc_data.description},
                    )

                # if lesson_data.description:
                #     for desc_data in lesson_data.description:
                #         LessonIntroduction.objects.update_or_create(
                #             id=desc_data.id,
                #             lesson=lesson,
                #             defaults={"introduction": desc_data.introduction},
                #         )

                # Quizy
                # Quizy
                if lesson_data.quizzes:
                    # Usuń stare quizy, które nie są już obecne
                    existing_quiz_ids = {question.id for question in lesson.lesson_quiz.all()}
                    incoming_quiz_ids = {question.id for question in lesson_data.quizzes if question.id is not None}
                    LessonQuiz.objects.filter(id__in=existing_quiz_ids - incoming_quiz_ids).delete()

                    for quiz_data in lesson_data.quizzes:
                        if quiz_data.id:
                            quiz = LessonQuiz.objects.get(id=quiz_data.id, lesson=lesson)
                            quiz.question = quiz_data.question
                            quiz.save()
                        else:
                            quiz = LessonQuiz.objects.create(
                                lesson=lesson,
                                question=quiz_data.question,
                            )

                        # Opcje quizów
                        existing_option_ids = {option.id for option in quiz.options.all()}
                        incoming_option_ids = {option.id for option in quiz_data.options if option.id is not None}
                        QuizOption.objects.filter(id__in=existing_option_ids - incoming_option_ids).delete()

                        for option_data in quiz_data.options:
                            QuizOption.objects.update_or_create(
                                id=option_data.id,
                                quiz=quiz,  # Poprawiono: zamiast quiz używamy question
                                defaults={"answer": option_data.answer, "is_correct": option_data.is_correct},
                            )


                # Zadanie
                if lesson_data.assignment:
                    for assignment_data in lesson_data.assignment:
                        LessonAssignment.objects.update_or_create(
                            id=assignment_data.id,
                            lesson=lesson,
                            defaults={"instructions": assignment_data.instructions},
                        )

        return 200, course.to_dict()
    except Course.DoesNotExist:
        return 404, {"message": f"Course with id {course_id} not found or unauthorized."}
    except Exception as e:
        traceback.print_exc()
        return 500, {"message": f"An error occurred: {str(e)}"}
