import traceback
from typing import List
from ninja import Query, Router
from django.db import transaction
from django.db.models import Count, Avg

from authentication.models import User
from lesson.models import Lesson, StudentProgress
from lesson_content.models import LessonAssignment, LessonIntroduction, LessonQuiz, QuizOption
from module.schemas import ModuleCreateSchema, ModuleResponseSchema

from .models import Course, Rating
from module.models import Module
from .schemas import CourseCreateSchema, CourseProgressSchema, CourseUpdateSchema, CourseDetailSchema, GeneralProgressStatsSchema, LessonProgressStatsSchema, RatingSchema, CourseDeatilUpdateSchema, CoursePreviewSchema, StatsSchema, EnrolledCourseProgressSchema
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
    
    
@router.get('', response={200: list[CoursePreviewSchema], 400: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def get_list_public_courses(request, sortBy: str = None, limit: int = None):
    """Retrieves a list of all public courses. Or if param is `option=my` retrieves only my course."""

    try:
        user = request.user
      
        if sortBy == "my":
            courses = Course.objects.filter(author=user).order_by('-last_updated')
        elif sortBy == "latest":
            courses = Course.objects.filter(is_public=True).order_by('-last_updated')
        elif sortBy == "highest-rated":
            courses = Course.objects.filter(is_public=True).order_by('-rating')
        elif sortBy == "most-popular":
            courses = Course.objects.filter(is_public=True).annotate(student_count=Count('students')).order_by('-student_count')
        elif sortBy == "enrolled":
            courses = Course.objects.filter(students=user).order_by('-last_updated')
        elif sortBy is not None:
            return 400, {"message": "Param is not valid. Choose from: 'my', 'latest', 'highest-rated', 'most-popular'."}
        else:
            
            public_courses = Course.objects.filter(is_public=True)
            user_courses = Course.objects.filter(author=user)
            courses = public_courses | user_courses
            courses = courses.distinct().order_by('-last_updated')
        
        if limit:
            courses = courses[:limit]

        return 200, [CourseDetailSchema(**course.to_dict()) for course in courses]
    except Exception as e:
        traceback.print_exc()
        return 500, {"message": "An unexpected error occurred while retrieving courses."}
    

@router.get('/stats', response={200: StatsSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def get_public_course(request):
    """Retrieves stats of all courses."""

    try:
        courses_count = Course.objects.filter().count()
        students_count = User.objects.filter(role="USER").count()
        completed_lessons = StudentProgress.objects.filter(lesson_completed=True).count()
        
        return 200, {
                "courses_count": courses_count,
                "students_count": students_count,
                "completed_lessons": completed_lessons
        }
    except Course.DoesNotExist:
        return 404, {"message": f"No stats found."}
    except Exception as e:
        traceback.print_exc()
        return 500, {"message": "An unexpected error occurred during course getting."}
   

@router.get('/enrolled', response={200: list[int], 500: MessageSchema}, auth=helpers.auth_required)
def get_enrolled_courses(request):
    """Retrieves list of IDs of all courses the user is enrolled in."""

    try:
        user = request.user

        enrolled_course_ids = Course.objects.filter(students=user).values_list('id', flat=True)

        return 200, list(enrolled_course_ids)
    except Exception as e:
        traceback.print_exc()
        return 500, {"message": "An unexpected error occurred while retrieving enrolled courses."}


@router.get('/{course_id}', response={200: CourseDetailSchema, 404: MessageSchema, 403: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def get_public_course(request, course_id: int):
    """Retrieves details of a specific public course by `course_id`, or private course if the user is the author."""

    try:
        user = request.user

        course = Course.objects.get(id=course_id)

        if not course.is_public and course.author != user:
            return 403, {"message": "You are not authorized to access this course."}

        return 200, course.to_dict()

    except Course.DoesNotExist:
        return 404, {"message": f"No course found with id {course_id}."}
    except Exception as e:
        traceback.print_exc()
        return 500, {"message": "An unexpected error occurred during course retrieval."}


@router.patch('/{course_id}', response={200: CourseDetailSchema, 400: MessageSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def update_my_course(request, payload: CourseDeatilUpdateSchema, course_id: int):
    """Updates details of a specific course with `course_id` created by the authenticated user."""

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


@router.post('/{course_id}/enroll', response={200: MessageSchema, 400: MessageSchema, 403: MessageSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def enroll_student(request, course_id: int):
    """Enrolls the authenticated user in a public course."""

    try:
        with transaction.atomic():
            course = Course.objects.get(id=course_id)

            if not course.is_public and course.author != request.user:
                return 403, {"message": "You are not authorized to access this course."}

            if request.user in course.students.all():
                return 400, {"message": "Already enrolled in this course."}

            course.students.add(request.user)

            first_module = course.modules.order_by('order').first()
            if not first_module:
                return 400, {"message": "The course does not contain any modules."}

            first_lesson = first_module.lessons.order_by('order').first()
            if not first_lesson:
                return 400, {"message": "The first module does not contain any lessons."}

            StudentProgress.objects.get_or_create(
                user=request.user,
                lesson=first_lesson,
                defaults={
                    "introduction_completed": False,
                    "quiz_score": None,
                    "assignment_score": None,
                    "lesson_completed": False,
                },
            )

            return 200, {"message": "Successfully enrolled in the course and progress initialized for the first lesson."}
    except Course.DoesNotExist:
        return 404, {"message": f"No public course found with id {course_id}."}
    except Exception as e:
        traceback.print_exc()
        return 500, {"message": "An unexpected error occurred during enrollment in the course."}
    
    
@router.get('/{course_id}/is-enrolled', response={200: dict, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def is_student_enrolled(request, course_id: int):
    """Checks if the authenticated student is enrolled in a specific course."""

    try:
        user = request.user

        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return 404, {"message": f"No course found with id {course_id}."}

        is_enrolled = course.students.filter(id=user.id).exists()

        return 200, {"is_enrolled": is_enrolled}
    except Exception as e:
        traceback.print_exc()
        return 500, {"message": "An unexpected error occurred while checking enrollment status."}
    

@router.post('/{course_id}/rate', response={200: MessageSchema, 400: MessageSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def rate_course(request, course_id: int, payload: RatingSchema):
    """Allows an enrolled user to rate a public course."""

    try:
        course = Course.objects.get(id=course_id)

        if not course.students.filter(id=request.user.id).exists():
            return 400, {"message": "Only enrolled users can rate this course."}
        
        rating = Rating.objects.update_or_create(
            course=course,
            user=request.user,
            defaults={'score': payload.score}
        )

        Course.update_course_rating(course_id)

        return 200, {"message": "Course rated successfully."}
    except Course.DoesNotExist:
        return 404, {"message": f"No public course found with id {course_id}."}
    except Exception as e:
        traceback.print_exc
        return 500, {"message": "An unexpected error occurred during the course rating process."}
    

@router.put("/{course_id}", response={200: CourseDetailSchema, 404: MessageSchema, 400: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def update_course(request, course_id: int, payload: CourseUpdateSchema):
    """Updates an entire course."""

    try:
        course = Course.objects.get(id=course_id, author=request.user)
        course.name = payload.name
        course.description = payload.description
        course.image = payload.image
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


@router.get("/progress/general", response={200: list[GeneralProgressStatsSchema], 500: MessageSchema}, auth=helpers.auth_required)
def get_general_progress_stats(request):
    """Retrieves progress statistics for all students across all courses."""

    try:
        users = User.objects.all()

        stats = []
        for user in users:
            progress = StudentProgress.objects.filter(user=user)
            lessons = Lesson.objects.filter(studentprogress__user=user).distinct()

            completed_lessons = progress.filter(lesson_completed=True).count()
            started_assignments = progress.exclude(assignment_score__isnull=True).count()
            started_quizzes = progress.exclude(quiz_score__isnull=True).count()

            assignment_scores = progress.filter(assignment_score__isnull=False).aggregate(avg_score=Avg('assignment_score'))['avg_score'] or 0
            quiz_scores = progress.filter(quiz_score__isnull=False).aggregate(avg_score=Avg('quiz_score'))['avg_score'] or 0

            stats.append(
                GeneralProgressStatsSchema(
                    username=user.username,
                    completed_lessons=completed_lessons,
                    started_assignments=started_assignments,
                    started_quizzes=started_quizzes,
                    assignment_score_percentage=assignment_scores,
                    quiz_score_percentage=quiz_scores,
                    lesson_count=progress.count(),
                )
            )

        return 200, stats

    except Exception as e:
        traceback.print_exc()
        return 500, {"message": f"An unexpected error occurred: {str(e)}"}

@router.get("/progress/enrolled", response={200: list[EnrolledCourseProgressSchema], 500: MessageSchema}, auth=helpers.auth_required)
def get_progress_in_enrolled_courses(request):
    """
    Retrieves progress statistics for all participants in courses the authenticated user is enrolled in.
    """
    try:
        user = request.user

        enrolled_courses = Course.objects.filter(students=user)

        if not enrolled_courses.exists():
            return 200, []

        response_data = []

        for course in enrolled_courses:
            lessons = Lesson.objects.filter(module__course=course)

            users = User.objects.filter(studentprogress__lesson__in=lessons).distinct()

            users_progress = []
            for enrolled_user in users:
                progress = StudentProgress.objects.filter(user=enrolled_user, lesson__in=lessons)

                completed_lessons = progress.filter(lesson_completed=True).count()
                started_assignments = progress.exclude(assignment_score__isnull=True).count()
                started_quizzes = progress.exclude(quiz_score__isnull=True).count()

                assignment_scores = progress.filter(assignment_score__isnull=False).aggregate(avg_score=Avg('assignment_score'))['avg_score'] or 0
                quiz_scores = progress.filter(quiz_score__isnull=False).aggregate(avg_score=Avg('quiz_score'))['avg_score'] or 0

                users_progress.append(
                    GeneralProgressStatsSchema(
                        username=enrolled_user.username,
                        completed_lessons=completed_lessons,
                        started_assignments=started_assignments,
                        started_quizzes=started_quizzes,
                        assignment_score_percentage=assignment_scores,
                        quiz_score_percentage=quiz_scores,
                        lesson_count=progress.count(),
                    )
                )

            response_data.append(
                EnrolledCourseProgressSchema(
                    course_id=course.id,
                    course_name=course.name,
                    users_progress=users_progress
                )
            )

        return 200, response_data

    except Exception as e:
        traceback.print_exc()
        return 500, {"message": f"An unexpected error occurred: {str(e)}"}


@router.get("/teacher/progress", response={200: List[CourseProgressSchema], 500: MessageSchema}, auth=helpers.auth_required)
def get_teacher_course_progress(request):
    """
    Retrieves aggregated progress statistics for all courses authored by the teacher.
    """
    try:
        user = request.user

        courses = Course.objects.filter(author=user)

        if not courses.exists():
            return 200, []

        response_data = []

        for course in courses:
            lessons = Lesson.objects.filter(module__course=course)

            lesson_progress = []
            for lesson in lessons:
                progress = StudentProgress.objects.filter(lesson=lesson)

                completed_lessons = progress.filter(lesson_completed=True).count()
                assignment_scores = progress.filter(assignment_score__isnull=False).aggregate(
                    avg_score=Avg('assignment_score')
                )['avg_score'] or 0
                quiz_scores = progress.filter(quiz_score__isnull=False).aggregate(
                    avg_score=Avg('quiz_score')
                )['avg_score'] or 0

                lesson_progress.append(
                    LessonProgressStatsSchema(
                        lesson_id=lesson.id,
                        lesson_topic=lesson.topic,
                        completed_lessons=completed_lessons,
                        assignment_score_percentage=assignment_scores,
                        quiz_score_percentage=quiz_scores,
                        lesson_count=progress.count(),
                    )
                )

            response_data.append(
                CourseProgressSchema(
                    course_id=course.id,
                    course_name=course.name,
                    lesson_progress=lesson_progress,
                )
            )

        return 200, response_data

    except Exception as e:
        traceback.print_exc()
        return 500, {"message": f"An unexpected error occurred: {str(e)}"}


@router.get("/{course_id}/progress", response={200: list[GeneralProgressStatsSchema], 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def get_course_progress_stats(request, course_id: int):
    """Retrieves progress statistics for all students in a specific course."""

    try:
        modules = Module.objects.filter(course_id=course_id)
        lessons = Lesson.objects.filter(module__in=modules)

        if not lessons.exists():
            return 404, {"message": f"No lessons found for course {course_id}."}

        users = User.objects.filter(studentprogress__lesson__in=lessons).distinct()

        stats = []
        for user in users:
            progress = StudentProgress.objects.filter(user=user, lesson__in=lessons)

            completed_lessons = progress.filter(lesson_completed=True).count()
            started_assignments = progress.exclude(assignment_score__isnull=True).count()
            started_quizzes = progress.exclude(quiz_score__isnull=True).count()

            assignment_scores = progress.filter(assignment_score__isnull=False).aggregate(avg_score=Avg('assignment_score'))['avg_score'] or 0
            quiz_scores = progress.filter(quiz_score__isnull=False).aggregate(avg_score=Avg('quiz_score'))['avg_score'] or 0

            stats.append(
                GeneralProgressStatsSchema(
                    username=user.username,
                    completed_lessons=completed_lessons,
                    started_assignments=started_assignments,
                    started_quizzes=started_quizzes,
                    assignment_score_percentage=assignment_scores,
                    quiz_score_percentage=quiz_scores,
                    lesson_count=lessons.count(),

                )
            )

        return 200, stats

    except Exception as e:
        traceback.print_exc()
        return 500, {"message": f"An unexpected error occurred: {str(e)}"}


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