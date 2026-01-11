from fastapi import APIRouter, Response
from pydantic import BaseModel
from typing import Dict, Optional
from app.services.health_service import HealthCheckService

router = APIRouter()


class ComponentHealth(BaseModel):
    status: str
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    message: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    checks: Dict[str, ComponentHealth]


@router.get("/")
def health_check():
    """Quick health check endpoint."""
    service = HealthCheckService()
    health = service.get_full_health()
    return health


@router.get("/live")
def liveness_probe():
    """Kubernetes liveness probe - is the process running?"""
    return {"status": "ok"}


@router.get("/ready")
def readiness_probe(response: Response):
    """Kubernetes readiness probe - can we serve traffic?"""
    service = HealthCheckService()
    db_health = service.check_database()
    
    if db_health.get("status") != "healthy":
        response.status_code = 503
        return {"status": "not_ready", "reason": "database unhealthy"}
    
    return {"status": "ready"}


@router.get("/database")
def database_health():
    """Database health check."""
    service = HealthCheckService()
    return service.check_database()


@router.get("/redis")
def redis_health():
    """Redis health check."""
    service = HealthCheckService()
    return service.check_redis()


@router.get("/llm")
def llm_health():
    """LLM service health check."""
    service = HealthCheckService()
    return service.check_llm()


@router.get("/worker")
def worker_health():
    """Worker health check."""
    service = HealthCheckService()
    return service.check_worker()
