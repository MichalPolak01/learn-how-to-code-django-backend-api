from ninja import Router
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError

from .models import User
from .schemas import UserCreateSchema, UserDetailSchema, MessageSchema


router = Router()


@router.post("/register", response= {201: UserDetailSchema, 400: MessageSchema})
def register(request, payload: UserCreateSchema):
    try:
        if User.objects.filter(email=payload.email).exists():
            return 400, {"message": "Email is already registered."}
        
        if User.objects.filter(username=payload.username).exists():
            return 400, {"message": "Username is already registered."}

        user_data = payload.dict()

        user_data['password'] = make_password(user_data['password'])

        user = User.objects.create(**user_data)

        return 201, user
    except ValidationError as e:
        return 400, {"message": str(e)}
    except Exception as e:
        return 400, {"message": "An unexpected error occurred."}