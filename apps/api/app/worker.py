import time
import logging
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.job import Job
from app.services.workers import process_send_email_job, process_sync_email_job, generate_draft_job, process_bulk_draft_orchestrator, generate_embedding_job

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_worker():
    logger.info("Starting Worker...")
    while True:
        db = SessionLocal()
        try:
            # Fetch pending job
            # For simplicity, FIFO. In production, use SELECT FOR UPDATE SKIP LOCKED
            job = db.query(Job).filter(Job.status == "pending").order_by(Job.created_at.asc()).first()
            
            if job:
                logger.info(f"Processing Job {job.id} (Type: {job.type})")
                job_type = job.type
                job_id = job.id
                db.close() # Close session before processing to allow worker function to manage its own session/transaction
                
                if job_type == "send_email":
                    process_send_email_job(job_id)
                elif job_type == "sync_email":
                    process_sync_email_job(job_id)
                elif job_type == "generate_draft":
                    generate_draft_job(job_id)
                elif job_type == "bulk_draft_orchestrator":
                    process_bulk_draft_orchestrator(job_id)
                elif job_type == "generate_embedding":
                    generate_embedding_job(job_id)
                else:
                    logger.warning(f"Unknown job type: {job_type}")
                    # Mark as failed
                    with SessionLocal() as db_fail:
                        j = db_fail.query(Job).filter(Job.id == job_id).first()
                        if j:
                            j.status = "failed"
                            j.error = "Unknown job type"
                            db_fail.commit()
            else:
                # No jobs, sleep
                db.close()
                time.sleep(2)
                
        except Exception as e:
            logger.error(f"Worker Loop Error: {e}")
            time.sleep(5)
        finally:
            # Session already closed in logic paths, but safe keeping
            pass

if __name__ == "__main__":
    run_worker()
