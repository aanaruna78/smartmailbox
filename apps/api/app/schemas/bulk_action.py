from pydantic import BaseModel
from typing import List

class BulkDraftRequest(BaseModel):
    email_ids: List[int]
    instructions: str
    tone: str = "professional"
