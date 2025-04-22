import time
from typing import List, Dict, Any, Optional
import os
from jira import JIRA
from pydantic import BaseModel

from config import config
from observability import logger, TICKETS_PROCESSED

class JiraTicket(BaseModel):
    id: str
    key: str
    summary: str
    description: Optional[str] = None
    reporter: Optional[str] = None
    created: Optional[str] = None
    labels: List[str] = []

class JiraClient:
    """Client for interacting with JIRA API."""
    
    def __init__(self):
        self.config = config.jira
        self.client = None
        self.use_mock = not bool(self.config.api_token)
        
        if not self.use_mock:
            try:
                self.client = JIRA(
                    server=self.config.base_url,
                    basic_auth=(self.config.user_email, self.config.api_token)
                )
                logger.info("JIRA client initialized", use_mock=False)
            except Exception as e:
                logger.error("Failed to initialize JIRA client", error=str(e))
                self.use_mock = True
        
        if self.use_mock:
            logger.info("Using mock JIRA client", use_mock=True)
    
    def get_feedback_tickets(self, jql: str, max_results: int = 50) -> List[JiraTicket]:
        """Fetch feedback tickets from JIRA based on JQL query."""
        logger.info("Fetching JIRA tickets", jql=jql, max_results=max_results, use_mock=self.use_mock)
        
        if self.use_mock:
            return self._get_mock_tickets(max_results)
        
        try:
            all_issues = []
            start_at = 0
            
            while True:
                issues = self.client.search_issues(jql, startAt=start_at, maxResults=50)
                if not issues:
                    break
                
                all_issues.extend(issues)
                TICKETS_PROCESSED.inc(len(issues))
                
                if len(issues) < 50 or len(all_issues) >= max_results:
                    break
                
                start_at += 50
                # Respect rate limits
                time.sleep(0.5)
            
            # Limit to max_results
            all_issues = all_issues[:max_results]
            
            # Convert to JiraTicket model
            return [
                JiraTicket(
                    id=str(issue.id),
                    key=issue.key,
                    summary=issue.fields.summary,
                    description=issue.fields.description or "",
                    reporter=issue.fields.reporter.displayName if issue.fields.reporter else None,
                    created=str(issue.fields.created) if hasattr(issue.fields, "created") else None,
                    labels=issue.fields.labels if hasattr(issue.fields, "labels") else []
                )
                for issue in all_issues
            ]
            
        except Exception as e:
            logger.error("Error fetching JIRA tickets", error=str(e))
            return self._get_mock_tickets(max_results=3)  # Return some mock data as fallback
    
    def _get_mock_tickets(self, max_results: int = 5) -> List[JiraTicket]:
        """Generate mock JIRA tickets for development/testing."""
        mock_tickets = [
            JiraTicket(
                id="10001",
                key="UX-101",
                summary="Difficult to find the export button",
                description="I was trying to export my data but couldn't find the button anywhere. After 5 minutes of searching, I found it hidden in a submenu. This should be more prominent.",
                reporter="Jane Smith",
                created="2023-11-01T10:30:00.000+0000",
                labels=["ux-feedback", "export"]
            ),
            JiraTicket(
                id="10002",
                key="UX-102",
                summary="Dashboard loads too slowly",
                description="Every time I log in, the dashboard takes at least 10 seconds to load. This is frustrating when I need to quickly check something.",
                reporter="John Doe",
                created="2023-11-02T14:15:00.000+0000",
                labels=["ux-feedback", "performance"]
            ),
            JiraTicket(
                id="10003",
                key="UX-103",
                summary="Love the new dark mode feature",
                description="The dark mode you added in the last update is fantastic! It's easier on my eyes when working late at night. Great job!",
                reporter="Alex Johnson",
                created="2023-11-03T09:45:00.000+0000",
                labels=["ux-feedback", "positive"]
            ),
            JiraTicket(
                id="10004",
                key="UX-104",
                summary="Search functionality doesn't find relevant results",
                description="When I search for keywords that I know exist in my documents, the search often returns no results or irrelevant ones. The search algorithm needs improvement.",
                reporter="Sarah Williams",
                created="2023-11-04T11:20:00.000+0000",
                labels=["ux-feedback", "search"]
            ),
            JiraTicket(
                id="10005",
                key="UX-105",
                summary="Need bulk edit feature for tasks",
                description="Currently I have to edit each task individually which is time-consuming. It would be great to have a way to select multiple tasks and edit them all at once.",
                reporter="Mike Brown",
                created="2023-11-05T16:00:00.000+0000",
                labels=["ux-feedback", "feature-request"]
            )
        ]
        
        return mock_tickets[:max_results]

# Initialize a global instance of the client
jira_client = JiraClient()

def get_jira_feedback(jql: str, max_results: int = 50) -> List[Dict[str, Any]]:
    """Tool to fetch JIRA feedback tickets based on JQL query."""
    tickets = jira_client.get_feedback_tickets(jql, max_results)
    # Convert to dict for easier use with the agent
    return [ticket.model_dump() for ticket in tickets] 