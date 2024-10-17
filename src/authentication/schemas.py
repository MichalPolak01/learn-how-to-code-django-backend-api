from ninja import Schema
from pydantic import EmailStr, Field, field_validator
import re


class UserCreateSchema(Schema):
    username: str = Field(min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(min_length=8)
    role: str

    @field_validator("password")
    def validate_password(cls, value):       
        if not re.search(r'[A-Z]', value):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not re.search(r'[0-9]', value):
            raise ValueError("Password must contain at least one digit")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise ValueError("Password must contain at least one special character")
        
        return value
    
    @field_validator("role")
    def validate_role(cls, value):
        allowed_roles = ["USER", "TEACHER", "ADMIN"]

        if value not in allowed_roles:
            raise ValueError(f"Invalid role: {value}")

        return value
    

class UserDetailSchema(Schema):
    id: int
    username: str
    email: EmailStr
    role: str


class MessageSchema(Schema):
    message: str