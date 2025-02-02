from fastapi import FastAPI, Depends, HTTPException
from database import users_collection
from auth import hash_password, verify_password, create_jwt_token, get_current_user
from services import start_service, stop_service, register_service
from models import UserRegister, UserLogin, ServiceModel
import datetime

app = FastAPI()

@app.post("/api/register")
async def register(user: UserRegister):
    """Register a new user."""
    existing_user = await users_collection.find_one({"username": user.username})
    if existing_user:
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

    token = await create_jwt_token({"sub": user.username, "role": existing_user["role"]}, expires_delta=datetime.timedelta(hours=1))
    return {"access_token": token, "token_type": "bearer"}

@app.post("/api/services/register")
async def add_service(service: ServiceModel, user=Depends(get_current_user)):
    """Register a new service (Admin Only)."""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can register services")
    return await register_service(service.name, service.image, service.description)

@app.post("/api/services/start/{service_name}")
async def start(service_name: str, user=Depends(get_current_user)):
    """Start a service (Admin Only)."""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can start services")
    return await start_service(service_name)

@app.post("/api/services/stop/{service_name}")
async def stop(service_name: str, user=Depends(get_current_user)):
    """Stop a service (Admin Only)."""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can stop services")
    return await stop_service(service_name)

@app.get("/api/services/list")
async def list_running_services(user=Depends(get_current_user)):
    """List all running services (Admin Only)."""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view services")
    return await list_services()

@app.get("/api/services/logs/{service_name}")
async def service_logs(service_name: str, user=Depends(get_current_user)):
    """Fetch logs from a running service (Admin Only)."""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view logs")
    return await get_service_logs(service_name)

@app.get("/api/services/stats/{service_name}")
async def service_stats(service_name: str, user=Depends(get_current_user)):
    """Fetch resource usage for a service (Admin Only)."""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view stats")
    return await get_service_stats(service_name)

@app.get("/api/services/health/{service_name}")
async def service_health(service_name: str, user=Depends(get_current_user)):
    """Check the health of a specific service (Admin Only)."""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view service health")
    return await check_service_health(service_name)

@app.get("/api/services/health/all")
async def all_services_health(user=Depends(get_current_user)):
    """Check the health of all services (Admin Only)."""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view service health")
    return await check_all_services_health()

@app.post("/api/services/restart_unhealthy")
async def restart_unhealthy(user=Depends(get_current_user)):
    """Restart all unhealthy services (Admin Only)."""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can restart services")
    return await restart_unhealthy_services()