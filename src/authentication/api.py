from ninja import Router
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from ninja.errors import HttpError
from ninja_jwt.tokens import RefreshToken

from .models import User
from .schemas import RegisterSchema, UserDetailSchema, MessageSchema, LoginSchema, UserUpdateSchema
import helpers

router = Router()


@router.post("/register", response= {201: UserDetailSchema, 400: MessageSchema})
def register(request, payload: RegisterSchema):
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
    

@router.post("/login", response={200: dict, 401: MessageSchema})
def login(request, payload: LoginSchema):
    user = authenticate(request, email=payload.email, password=payload.password)

    if user is None:
        return 401, {"message": "Invalid email or password"}
    
    refresh = RefreshToken.for_user(user)

    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "username": user.username
    }


@router.patch("/user/update", response={200: UserDetailSchema, 400: MessageSchema}, auth=helpers.auth_required)
def update_user(request, payload: UserUpdateSchema):
    try:
        user = request.user

        if payload.email and User.objects.filter(email=payload.email).exclude(id=user.id).exists():
            return 400, {"message": "Email is already taken."}
        
        if payload.username and User.objects.filter(username=payload.username).exclude(id=user.id).exists():
            return 400, {"message": "Username is already taken."}

        for attr, value in payload.dict(exclude_unset=True).items():
            setattr(user, attr, value)

        user.save()

        return 200, user
    
    except ValidationError as e:
        return 400, {"message": str(e)}
    except Exception as e:
        return 400, {"message": "An unexpected error occurred."}