from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class UserMeResponse(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)