from typing import Annotated

from pydantic import BaseModel, EmailStr, SecretStr, StringConstraints

Password = Annotated[SecretStr, StringConstraints(min_length=12, max_length=128)]


class RegisterRequest(BaseModel):
    email: EmailStr
    password: Password


class LoginRequest(BaseModel):
    email: EmailStr
    password: Password
