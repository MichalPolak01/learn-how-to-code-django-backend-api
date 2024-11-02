from ninja import Router

from .models import Course, Rating
from .schemas import CourseCreateSchema, CourseDetailSchema
from learn_how_to_code.schemas import MessageSchema
import helpers

router = Router()


@router.post("", response={201: CourseDetailSchema, 400: MessageSchema}, auth=helpers.auth_required)
def create_course(request, payload: CourseCreateSchema):
    """
        Endpoint to create a new course.
        
        Allows authenticated users with a 'TEACHER' role to create a course.
        The course name must be unique within the database.
    """
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
        return 400, {"message": "An unexpected error occurred during course creation."}