from typing import Dict, List, Any
from pydantic import BaseModel

from observability import logger

class UserStoryResponse(BaseModel):
    title: str
    description: str
    acceptance_criteria: List[str]

# Note: These functions are now implemented directly in the agent.py file
# They are kept here as reference but are no longer used 