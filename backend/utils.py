from enum import StrEnum


class ServiceStatus(StrEnum):
    Running = "Running"
    Stopped = "Stoppped"
    Unhealthy = "Unhealthy"
    Other = "Other"
