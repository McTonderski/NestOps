from pydantic import BaseModel


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
    description: str | None = None


class ServiceStatus(BaseModel):
    pass


class SystemStatus(BaseModel):
    name: str
    cpu_stats: float | None = None
    ram_stats: float | None = None
    mem_stats: float | None = None
