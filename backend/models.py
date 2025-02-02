from pydantic import BaseModel
from typing import Optional

class UserRegister(BaseModel):
    username: str
    password: str
    role: str  # "admin" or "user"

class UserLogin(BaseModel):
    username: str
    password: str

class ServiceModel(BaseModel):
    name: str
    image: str
    description: Optional[str] = None