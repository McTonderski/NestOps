import docker
from backend.utils import ServiceStatus
from fastapi import HTTPException
from database import services_collection

client = docker.from_env()


async def start_service(service_name: str):
    """Start a Docker container from a registered service."""
    service = await services_collection.find_one({"name": service_name})
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    container = client.containers.run(
        service["image"], detach=True, name=service["name"]
    )
    service["status"] = ServiceStatus.Running
    # TODO: Add save to mongo
    return {"message": f"Service {service_name} started", "container_id": container.id}


async def stop_service(service_name: str):
    """Stop a running Docker container."""
    try:
        container = client.containers.get(service_name)
        container.stop()
        return {"message": f"Service {service_name} stopped"}
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Service not found")


async def register_service(name: str, image: str, description: str):
    """Register a new service (Admin Only)."""
    service_data = {"name": name, "image": image, "description": description}
    await services_collection.insert_one(service_data)
    return {"message": f"Service {name} registered"}


async def check_service_health(service_name: str):
    """Check the health status of a service."""
    try:
        container = client.containers.get(service_name)
        health_status = (
            container.attrs.get("State", {}).get("Health", {}).get("Status", "unknown")
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
    """Check the health of all running services."""
    containers = client.containers.list(all=True)
    health_report = []

    for container in containers:
        health_status = (
            container.attrs.get("State", {}).get("Health", {}).get("Status", "unknown")
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
    containers = client.containers.list(all=True)
    restarted_services = []

    for container in containers:
        health_status = (
            container.attrs.get("State", {}).get("Health", {}).get("Status", "unknown")
        )

        if health_status in ["unhealthy", "unknown"]:
            container.restart()
            restarted_services.append(container.name)

    return {"restarted_services": restarted_services}
