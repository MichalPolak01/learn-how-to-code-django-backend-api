from ninja import Router

from .models import Course, Rating
from .schemas import CourseCreateSchema, CourseUpdateSchema, CourseDetailSchema
from learn_how_to_code.schemas import MessageSchema
import helpers
import logging

logger = logging.getLogger(__name__)

router = Router()


@router.post("", response={201: CourseDetailSchema, 400: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def create_course(request, payload: CourseCreateSchema):
    """Endpoint to create a new course."""

    try:
        author = request.user

        if Course.objects.filter(name=payload.name).exists():
          return 400, {"message": "A course with this name already exists."}
        
        if author.role != "TEACHER":
            return 400, {"message": "Only teachers can create courses."}
        
        course_data = payload.dict()
        course_data['author'] = request.user

        course = Course.objects.create(**course_data)

        return 201, course.to_dict()
    except Exception as e:
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
        course = Course.objects.get(id=course_id, is_public=True)
        
        return 200, course.to_dict()
    except Course.DoesNotExist:
        return 404, {"message": f"No public course found with id {course_id}."}
    except Exception as e:
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