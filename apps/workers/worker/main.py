import time
import logging
from worker.tasks.sync_emails import sync_all_mailboxes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Worker started...")
    while True:
        try:
            sync_all_mailboxes()
        except Exception as e:
            logger.error(f"Error in sync task: {e}")
        
        # Poll every 60 seconds
        time.sleep(60)

if __name__ == "__main__":
    main()
