from typing import Dict, List, Any, Optional
import json
from pydantic import BaseModel
import asyncio

import openai
from openai import OpenAI

from config import config
from observability import logger, TICKETS_PROCESSED, RUN_DURATION, Timer
from tools.jira_tools import get_jira_feedback

# Initialize OpenAI client
client = OpenAI(api_key=config.openai_api_key)

class FeedbackAnalysisResult(BaseModel):
    ticket_id: str
    user_story: Dict[str, Any]
    pm_response: str

class JiraFeedbackAgent:
    """
    Agent that orchestrates the workflow to analyze JIRA feedback tickets.
    """
    
    def __init__(self, persist_thread: bool = False, user_id: Optional[str] = None):
        """
        Initialize the agent.
        
        Args:
            persist_thread: Whether to persist the agent thread across requests
            user_id: Optional user ID for personalization
        """
        self.persist_thread = persist_thread
        self.user_id = user_id
        self.thread_id = None
        self.status_callback = None
        
        logger.info("Initialized JIRA Feedback Agent", 
                   persist_thread=persist_thread, 
                   user_id=user_id)
    
    def set_status_callback(self, callback):
        """Set a callback function to receive real-time status updates."""
        self.status_callback = callback
        
    def update_status(self, step: str, message: str, data: Optional[Dict] = None):
        """Send a status update through the callback if available."""
        if self.status_callback:
            self.status_callback(step, message, data)
        logger.info(f"Status update: {step} - {message}")
    
    async def _create_user_story(self, summary: str, description: str) -> Dict[str, Any]:
        """Create a user story based on the feedback."""
        logger.info("Creating user story", summary=summary)
        
        self.update_status("user_story", "Generating user story from feedback...", None)
        
        # Use OpenAI to generate a user story
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """
You are a Product Manager Assistant. Convert customer feedback into a well-structured user story.
The user story should include:
1. Title (in the format "As a user, I want to...")
2. Description explaining the value and reasoning
3. 2-3 acceptance criteria that are testable and clear
"""},
                {"role": "user", "content": f"Feedback summary: {summary}\n\nFeedback description: {description}"}
            ],
            temperature=0.7
        )
        
        # Extract the response
        story_text = response.choices[0].message.content
        
        # Parse the response - normally we'd have a more robust parser
        # This is a simple version for demonstration
        try:
            lines = story_text.strip().split('\n')
            title = next((line for line in lines if "As a user" in line), "As a user, I want to improve my experience")
            
            # Extract description - assume it's between title and acceptance criteria
            start_idx = lines.index(title) + 1
            end_idx = next((i for i, line in enumerate(lines) if "acceptance criteria" in line.lower() or "criteria" in line.lower()), len(lines))
            description_lines = lines[start_idx:end_idx]
            description = "\n".join(description_lines).strip()
            
            # Extract acceptance criteria
            criteria = []
            for line in lines[end_idx:]:
                if line.strip() and ("- " in line or "* " in line or line[0].isdigit()):
                    criteria.append(line.replace("- ", "").replace("* ", "").strip())
            
            result = {
                "title": title.strip(),
                "description": description,
                "acceptance_criteria": criteria if criteria else ["Functionality works as expected", "User interface is intuitive", "Performance is optimized"]
            }
            
            self.update_status("user_story", "User story created successfully", result)
            
            # Add a pause to make the step visible
            await asyncio.sleep(2)
            
            return result
        except Exception as e:
            logger.error("Error parsing user story", error=str(e))
            result = {
                "title": "As a user, I want to " + summary.lower(),
                "description": "This feature would improve user experience by addressing the feedback provided.",
                "acceptance_criteria": ["Functionality works as expected", "UI is intuitive and user-friendly", "Performance is optimized"]
            }
            
            self.update_status("user_story", "Created fallback user story due to parsing error", result)
            
            # Add a pause to make the step visible
            await asyncio.sleep(2)
            
            return result
    
    async def _suggest_pm_response(self, ticket_id: str, summary: str, description: str = "") -> str:
        """Generate a PM response for a feedback ticket."""
        logger.info("Creating PM response", ticket_id=ticket_id, summary=summary)
        
        self.update_status("pm_response", "Generating PM response...", None)
        
        # Use OpenAI to generate a response
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """
You are a Product Manager responding to customer feedback. Write a brief, empathetic response that:
1. Thanks the user for their feedback
2. Acknowledges their specific concerns or compliments
3. Indicates what action will be taken (if appropriate)
4. Keeps the response under 3-4 sentences

Be professional, helpful, and concise.
"""},
                {"role": "user", "content": f"Ticket ID: {ticket_id}\nFeedback summary: {summary}\nFeedback description: {description}"}
            ],
            temperature=0.7
        )
        
        # Extract the response
        result = response.choices[0].message.content.strip()
        
        self.update_status("pm_response", "PM response generated successfully", {"response": result})
        
        # Add a pause to make the step visible
        await asyncio.sleep(2)
        
        return result
    
    async def analyze_feedback(self, jql: str, max_results: int = 50) -> List[FeedbackAnalysisResult]:
        """
        Analyze JIRA feedback tickets.
        
        Args:
            jql: JIRA Query Language string to filter tickets
            max_results: Maximum number of tickets to process
            
        Returns:
            List of feedback analysis results
        """
        with Timer(RUN_DURATION):
            logger.info("Starting feedback analysis", jql=jql, max_results=max_results)
            self.update_status("start", f"Starting feedback analysis for {max_results} tickets", {"jql": jql})
            
            # Get tickets from JIRA
            tickets_data = get_jira_feedback(jql, max_results)
            logger.info(f"Retrieved {len(tickets_data)} tickets")
            self.update_status("fetch", f"Retrieved {len(tickets_data)} tickets", {"count": len(tickets_data)})
            
            results = []
            
            # Process each ticket
            for index, ticket in enumerate(tickets_data):
                try:
                    self.update_status("processing", f"Processing ticket {index+1}/{len(tickets_data)}: {ticket['key']}", 
                                      {"ticket_id": ticket["key"], "progress": f"{index+1}/{len(tickets_data)}"})
                    
                    # Create user story
                    user_story = await self._create_user_story(
                        summary=ticket["summary"],
                        description=ticket.get("description", "")
                    )
                    
                    # Generate PM response
                    pm_response = await self._suggest_pm_response(
                        ticket_id=ticket["key"],
                        summary=ticket["summary"],
                        description=ticket.get("description", "")
                    )
                    
                    # Create result
                    result = FeedbackAnalysisResult(
                        ticket_id=ticket["key"],
                        user_story=user_story,
                        pm_response=pm_response
                    )
                    
                    results.append(result)
                    
                    # Log progress
                    logger.info("Processed ticket", ticket_id=ticket["key"])
                    self.update_status("ticket_complete", f"Completed processing ticket {ticket['key']}", 
                                      {"ticket_id": ticket["key"], "progress": f"{index+1}/{len(tickets_data)}"})
                    
                except Exception as e:
                    logger.error("Error processing ticket", ticket_id=ticket["key"], error=str(e))
                    self.update_status("error", f"Error processing ticket {ticket['key']}: {str(e)}", 
                                      {"ticket_id": ticket["key"], "error": str(e)})
            
            logger.info("Feedback analysis complete", ticket_count=len(results))
            self.update_status("complete", f"Feedback analysis complete - processed {len(results)} tickets", {"count": len(results)})
            return results 