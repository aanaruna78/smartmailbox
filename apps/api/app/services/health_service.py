import logging
from typing import Dict, Optional
from datetime import datetime
from sqlalchemy import text
from app.db.session import SessionLocal
from app.core.config import settings

logger = logging.getLogger(__name__)


class HealthCheckService:
    """
    Service for checking health of all system components.
    """
    
    def check_database(self) -> Dict:
        """Check database connectivity."""
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
            return {"status": "healthy", "latency_ms": 0}
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    def check_redis(self) -> Dict:
        """Check Redis connectivity."""
        try:
            import redis
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379')
            r = redis.from_url(redis_url)
            start = datetime.utcnow()
            r.ping()
            latency = (datetime.utcnow() - start).total_seconds() * 1000
            return {"status": "healthy", "latency_ms": round(latency, 2)}
        except ImportError:
            return {"status": "not_configured", "message": "Redis not installed"}
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    def check_llm(self) -> Dict:
        """Check LLM service availability."""
        try:
            import httpx
            llm_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
            response = httpx.get(f"{llm_url}/api/version", timeout=5.0)
            if response.status_code == 200:
                return {"status": "healthy", "version": response.json().get("version", "unknown")}
            return {"status": "degraded", "status_code": response.status_code}
        except ImportError:
            return {"status": "not_configured", "message": "httpx not installed"}
        except Exception as e:
            logger.error(f"LLM health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    def check_worker(self) -> Dict:
        """Check worker status by looking at recent job processing."""
        try:
            from app.models.job import Job
            db = SessionLocal()
            
            # Check for recently completed jobs
            from datetime import timedelta
            recent = datetime.utcnow() - timedelta(minutes=5)
            recent_jobs = db.query(Job).filter(
                Job.completed_at >= recent
            ).count()
            
            pending_jobs = db.query(Job).filter(Job.status == "pending").count()
            processing_jobs = db.query(Job).filter(Job.status == "processing").count()
            
            db.close()
            
            status = "healthy" if recent_jobs > 0 or pending_jobs == 0 else "degraded"
            return {
                "status": status,
                "pending_jobs": pending_jobs,
                "processing_jobs": processing_jobs,
                "recently_completed": recent_jobs
            }
        except Exception as e:
            logger.error(f"Worker health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    def check_api(self) -> Dict:
        """Check API health (always healthy if this runs)."""
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_full_health(self) -> Dict:
        """Get comprehensive health status."""
        checks = {
            "api": self.check_api(),
            "database": self.check_database(),
            "redis": self.check_redis(),
            "llm": self.check_llm(),
            "worker": self.check_worker()
        }
        
        # Overall status
        unhealthy = [k for k, v in checks.items() if v.get("status") == "unhealthy"]
        degraded = [k for k, v in checks.items() if v.get("status") == "degraded"]
        
        if unhealthy:
            overall = "unhealthy"
        elif degraded:
            overall = "degraded"
        else:
            overall = "healthy"
        
        return {
            "status": overall,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks
        }
