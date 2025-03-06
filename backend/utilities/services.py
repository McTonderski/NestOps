import os
import logging
import importlib
import pkgutil
import docker
from fastapi import HTTPException
from utilities.utils import ServiceStatus
from utilities.database import services_collection
from services.service_manager import AbstractDockerComposeManager

# Initialize Docker client
client = docker.from_env()

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

# Dictionary to hold available service managers
list_of_managers = {}


async def scan_for_services():
    """Dynamically discover and load all service managers from the 'services' directory and fetch their status from the DB."""
    global list_of_managers
    
    base_package = "services"
    current_dir = os.path.dirname(os.path.abspath(__file__))
    services_path = os.path.abspath(os.path.join(current_dir, "..", base_package))

    if not os.path.isdir(services_path):
        logging.error("Service directory not found")
        return

    for service in os.listdir(services_path):
        service_dir = os.path.join(services_path, service)
        if not os.path.isdir(service_dir) or service.startswith("_"):
            continue

        try:
            service_package = f"{base_package}.{service}"
            importlib.import_module(service_package)

            for _, module_name, _ in pkgutil.iter_modules([service_dir]):
                full_module_name = f"{service_package}.{module_name}"
                module = importlib.import_module(full_module_name)

                for attribute_name in dir(module):
                    attribute = getattr(module, attribute_name)
                    if (
                        isinstance(attribute, type)
                        and issubclass(attribute, AbstractDockerComposeManager)
                        and attribute is not AbstractDockerComposeManager
                    ):
                        db_service = await services_collection.find_one({"name": attribute.NAME})
                        list_of_managers[attribute.NAME.lower()] = attribute(service_dir)
                        status = list_of_managers[attribute.NAME.lower()].is_container_running()
                        if not db_service:
                            await services_collection.insert_one(
                                {
                                    "name": attribute.NAME,
                                    "image": None,
                                    "description": None,
                                    "status": ServiceStatus.Running if status else ServiceStatus.Stopped,
                                    "container_id": None,
                                }
                            )
        except ModuleNotFoundError:
            logging.warning(f"Skipping {service} (module not found)")

    logging.info(f"Loaded service managers: {list_of_managers}")


async def list_services():
    """Fetch all registered services from the database."""
    try:
        services = await services_collection.find({}).to_list(length=100)
        return [{"name": service["name"], "status": service["status"]} for service in services]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading services: {str(e)}")


async def start_service(service_name: str):
    """Start a service using its associated manager and update the database."""
    service = await services_collection.find_one({"name": {'$regex': service_name.lower(), '$options': 'i'}})
    manager: AbstractDockerComposeManager = list_of_managers.get(service_name)

    if not manager:
        logging.warning(f"Manager not found for: {service_name}")
        raise HTTPException(status_code=404, detail="Manager not found")
    if not service:
        logging.warning(f"Service not found: {service_name}")
        for service in await services_collection.find({}).to_list(length=100):
            logging.info(service)
        raise HTTPException(status_code=404, detail="Service not found")

    manager.run_docker_compose()

    await services_collection.update_one(
        {"name": {'$regex': service_name.lower(), '$options': 'i'}}, {"$set": {"status": "running"}}
    )
    return {"message": f"Service {service_name} started"}


async def stop_service(service_name: str):
    """Stop a running service and update the database."""
    service = await services_collection.find_one({"name": {'$regex': service_name.lower(), '$options': 'i'}})
    manager: AbstractDockerComposeManager = list_of_managers.get(service_name)

    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    manager.down_docker_compose()
    await services_collection.update_one(
        {"name": {'$regex': service_name.lower(), '$options': 'i'}}, {"$set": {"status": "stopped"}}
    )
    return {"message": f"Service {service_name} stopped"}


async def register_service(name: str, image: str, description: str):
    """Register a new service in the database."""
    if await services_collection.find_one({"name": name}):
        raise HTTPException(status_code=400, detail="Service already exists")

    await services_collection.insert_one(
        {
            "name": name,
            "image": image,
            "description": description,
            "status": "stopped",
            "container_id": None,
        }
    )
    return {"message": f"Service {name} registered successfully"}


async def check_service_health(service_name: str):
    """Check the health status of a specific service and update the database."""
    try:
        container = client.containers.get(service_name)
        health_status = container.attrs.get("State", {}).get("Health", {}).get("Status", "unknown")

        await services_collection.update_one(
            {"name": service_name}, {"$set": {"status": container.status, "health": health_status}}
        )

        return {
            "service": service_name,
            "status": container.status,
            "health": health_status,
            "started_at": container.attrs["State"]["StartedAt"],
        }
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Service not found")


async def check_all_services_health():
    """Check the health status of all running services and update the database."""
    health_report = []
    for container in client.containers.list(all=True):
        health_status = container.attrs.get("State", {}).get("Health", {}).get("Status", "unknown")

        await services_collection.update_one(
            {"name": container.name}, {"$set": {"status": container.status, "health": health_status}}
        )

        health_report.append(
            {
                "service": container.name,
                "status": container.status,
                "health": health_status,
                "started_at": container.attrs["State"]["StartedAt"],
            }
        )

    return health_report


async def restart_unhealthy_services():
    """Restart all unhealthy services."""
    restarted_services = []
    for container in client.containers.list(all=True):
        health_status = container.attrs.get("State", {}).get("Health", {}).get("Status", "unknown")

        if health_status in ["unhealthy", "unknown"]:
            container.restart()
            restarted_services.append(container.name)

    return {"restarted_services": restarted_services}