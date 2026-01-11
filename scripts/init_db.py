import sys
import os

# Add the project root to the python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))

from app.db.session import engine, Base
from app.models.user import User
from app.models.mailbox import Mailbox
from app.models.job import Job
from app.models.email import Email
from app.models.attachment import Attachment
from app.models.tag import Tag

def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

if __name__ == "__main__":
    init_db()
