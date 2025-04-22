import os
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

class JiraConfig(BaseModel):
    api_token: str
    base_url: str
    project_key: str
    user_email: str

class AppConfig(BaseModel):
    openai_api_key: str
    jira: JiraConfig

def load_config() -> AppConfig:
    """Load application configuration from environment variables."""
    return AppConfig(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        jira=JiraConfig(
            api_token=os.getenv("JIRA_API_TOKEN", ""),
            base_url=os.getenv("JIRA_BASE_URL", ""),
            project_key=os.getenv("JIRA_PROJECT_KEY", ""),
            user_email=os.getenv("JIRA_USER_EMAIL", "")
        )
    )

# Create a global config instance
config = load_config() 