import datetime
import json
import subprocess
import psutil
from copy import deepcopy
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from utilities import database
from utilities.auth import (
    hash_password,
    verify_password,
    create_jwt_token,
    get_current_user
)
from utilities.services import (
    start_service,
    stop_service,
    register_service,
    check_service_health,
    list_services,
    scan_for_services,
    restart_unhealthy_services,
    check_all_services_health
)
from utilities.models import UserRegister, UserLogin, ServiceModel

# MongoDB collections
users_collection = database.users_collection


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run service scan on startup."""
    await scan_for_services()
    yield


# FastAPI App
app = FastAPI(
    swagger_ui_parameters={"syntaxHighlight": False},
    docs_url="/api/docs",
    lifespan=lifespan,
)


# Utility function for admin-only endpoints
async def ensure_admin(user):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")


# Authentication Endpoints
@app.post("/api/register")
async def register(user: UserRegister):
    """Register a new user."""
    if await users_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_pw = await hash_password(user.password)
    user_data = {"username": user.username, "password": hashed_pw, "role": user.role}
    await users_collection.insert_one(user_data)
    return {"message": "User registered successfully"}


@app.post("/api/login")
async def login(user: UserLogin):
    """Authenticate user and return JWT."""
    existing_user = await users_collection.find_one({"username": user.username})
    if not existing_user or not await verify_password(user.password, existing_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = await create_jwt_token(
        {"sub": user.username, "role": existing_user["role"]},
        expires_delta=datetime.timedelta(hours=1),
    )
    return {"access_token": token, "token_type": "bearer"}


@app.post("/api/role")
async def change_role(user: UserRegister):
    """Change user role."""
    existing_user = await users_collection.find_one({"username": user.username})
    if not existing_user or not await verify_password(user.password, existing_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    await users_collection.update_one(
        {"username": user.username}, {"$set": {"role": user.role}}
    )

    return {"message": "User role updated successfully", "new_role": user.role}


# Service Management Endpoints (Admin Only)
@app.post("/api/services/register")
async def add_service(service: ServiceModel, user=Depends(get_current_user)):
    """Register a new service (Admin Only)."""
    await ensure_admin(user)
    return await register_service(service.name, service.image, service.description)


@app.post("/api/services/start/{service_name}")
async def start(service_name: str, user=Depends(get_current_user)):
    """Start a service (Admin Only)."""
    await ensure_admin(user)
    return await start_service(service_name.lower())


@app.post("/api/services/stop/{service_name}")
async def stop(service_name: str, user=Depends(get_current_user)):
    """Stop a service (Admin Only)."""
    await ensure_admin(user)
    return await stop_service(service_name.lower())


@app.get("/api/services/list")
async def list_running_services(user=Depends(get_current_user)):
    """List all running services (Admin Only)."""
    await ensure_admin(user)
    return await list_services()


@app.get("/api/services/health/{service_name}")
async def service_health(service_name: str, user=Depends(get_current_user)):
    """Check the health of a specific service (Admin Only)."""
    await ensure_admin(user)
    return await check_service_health(service_name.lower())


@app.get("/api/services/health/all")
async def all_services_health(user=Depends(get_current_user)):
    """Check the health of all services (Admin Only)."""
    await ensure_admin(user)
    return await check_all_services_health()


@app.post("/api/services/restart_unhealthy")
async def restart_unhealthy(user=Depends(get_current_user)):
    """Restart all unhealthy services (Admin Only)."""
    await ensure_admin(user)
    return await restart_unhealthy_services()


@app.get("/api/instance/details")
async def get_instance_details(user=Depends(get_current_user)):
    """Get system details like RAM, CPU usage, and running Docker containers."""
    cpu_usage = psutil.cpu_percent(interval=1)

    mem_info = psutil.virtual_memory()
    memory_usage = {
        "total": mem_info.total,
        "used": mem_info.used,
        "free": mem_info.available,
        "percent": mem_info.percent,
    }

    try:
        docker_output = subprocess.run(
            ["docker", "ps", "--all", "--format", "{{json .}}"],
            capture_output=True,
            text=True,
            check=True,
        )
        containers = [json.loads(line) for line in docker_output.stdout.splitlines()]
    except subprocess.CalledProcessError:
        containers = "Error retrieving Docker containers. Ensure Docker is installed and running."

    return {
        "cpu_usage_percent": cpu_usage,
        "memory_usage": memory_usage,
        "running_docker_containers": containers,
    }