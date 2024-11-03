from ninja_extra import Router

from .schemas import ModuleCreateSchema, ModuleUpdateSchema, ModuleDetailSchema
from learn_how_to_code.schemas import MessageSchema

from .models import Module
from course.models import Course

import helpers

router = Router()

@router.post("/{course_id}/modules", response={201: ModuleDetailSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def create_course(request, payload: ModuleCreateSchema, course_id: int):
    """Creates a new module within a specific course."""

    try:
        course = Course.objects.get(id=course_id, author=request.user)

        module_data = payload.dict()
        module_data['course'] = course
        module_data['order'] = Module.get_next_order(course_id)

        module = Module.objects.create(**module_data)

        return 201, module.to_dict()
    except Course.DoesNotExist:
        return 404, {"message": f"Course with id {course_id} not found for the current user."}
    except Exception as e:
        return 500, {"message": "An unexpected error occurred during course creation."}
    

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
        return 500, {"message": "An unexpected error occurred during course creation."}
    

@router.get('/{course_id}/modules/{module_id}', response={200: ModuleDetailSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def get_module(request, course_id: int, module_id: int):
    """Retrieves details of a specific module."""

    try:
        module = Module.objects.get(id=module_id, course=course_id)

        return 200, module.to_dict()
    except Course.DoesNotExist:
        return 404, {"message": f"Course with id {course_id} not found for the current user."}
    except Exception as e:
        return 500, {"message": "An unexpected error occurred during course creation."}
    

@router.patch('/{course_id}/modules/{module_id}', response={200: ModuleDetailSchema, 400: MessageSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def update_module(request, payload: ModuleUpdateSchema, course_id: int, module_id: int):
    """Updates details of a specific course created by the authenticated user."""

    try:
        module = Module.objects.get(id=module_id, course=course_id)
        
        for attr, value in payload.dict(exclude_unset=True).items():
            setattr(module, attr, value)

        module.save()

        return 200, module.to_dict()
    except Course.DoesNotExist:
        return 404, {"message": f"Course with id {course_id} not found for the current user."}
    except Exception as e:
        return 500, {"message": "An unexpected error occurred while updating the course."}