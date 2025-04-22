import os
import uuid
import time
import json
from typing import Dict, Any, List, Optional
import uvicorn
from fastapi import FastAPI, Response, Query, BackgroundTasks, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from prometheus_client import CONTENT_TYPE_LATEST

from agent import JiraFeedbackAgent, FeedbackAnalysisResult
from observability import logger, get_metrics, health_check
from tools.jira_tools import JiraClient, jira_client, JiraTicket

# Initialize FastAPI app
app = FastAPI(
    title="JIRA Feedback Analyzer",
    description="AI agent to analyze JIRA feedback and convert it to user stories",
    version="0.1.0",
)

class AnalyzeFeedbackRequest(BaseModel):
    jql: str
    max_results: int = 50

class AnalyzeFeedbackResponse(BaseModel):
    results: List[FeedbackAnalysisResult]

class StartWorkflowRequest(BaseModel):
    jql: str
    max_results: int = 3
    persist_thread: bool = False
    post_to_jira: bool = False
    mock_feedback_items: List[Dict[str, Any]] = []

class WorkflowStatus(BaseModel):
    workflow_id: str
    is_complete: bool
    current_status: str
    steps: List[Dict[str, Any]] = []
    results: List[Dict[str, Any]] = []
    tickets: List[Dict[str, Any]] = []

class JiraCommentRequest(BaseModel):
    ticket_id: str
    comment: str

# Agent instance cache by user_id
agent_cache = {}

# Workflow storage
workflows = {}

# Create static directory if it doesn't exist
os.makedirs("static", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def get_ui():
    """Serve the UI."""
    with open("static/index.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health():
    """Health check endpoint."""
    return health_check()

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(get_metrics(), media_type=CONTENT_TYPE_LATEST)

@app.post("/analyze-feedback", response_model=AnalyzeFeedbackResponse)
async def analyze_feedback(
    request: AnalyzeFeedbackRequest,
    persist_thread: bool = Query(False, description="Whether to persist the agent thread across requests"),
    user_id: Optional[str] = Query(None, description="Optional user ID for personalization")
):
    """
    Analyze JIRA feedback tickets and convert them to user stories.
    
    - **jql**: JIRA Query Language string to filter tickets
    - **max_results**: Maximum number of tickets to process (default: 50)
    - **persist_thread**: Whether to persist the agent thread across requests
    - **user_id**: Optional user ID for personalization
    """
    logger.info("Received analyze feedback request", 
               jql=request.jql, 
               max_results=request.max_results,
               persist_thread=persist_thread,
               user_id=user_id)
    
    # Get or create agent instance
    agent_key = f"{user_id}" if user_id else "default"
    if persist_thread and agent_key in agent_cache:
        agent = agent_cache[agent_key]
    else:
        agent = JiraFeedbackAgent(persist_thread=persist_thread, user_id=user_id)
        if persist_thread:
            agent_cache[agent_key] = agent
    
    # Run analysis
    results = agent.analyze_feedback(request.jql, request.max_results)
    
    return AnalyzeFeedbackResponse(results=results)

@app.post("/workflow/start", response_model=Dict[str, str])
async def start_workflow(request: StartWorkflowRequest, background_tasks: BackgroundTasks):
    """
    Start a new agent workflow.
    """
    workflow_id = str(uuid.uuid4())
    
    # Initialize workflow data
    workflows[workflow_id] = {
        "is_complete": False,
        "current_status": "Initializing agent...",
        "steps": [],
        "results": [],
        "tickets": [],
        "timestamp": time.time(),
        "request": request.model_dump()
    }
    
    # Run the workflow in the background
    background_tasks.add_task(run_workflow, workflow_id)
    
    return {"workflow_id": workflow_id}

@app.get("/workflow/{workflow_id}/status", response_model=WorkflowStatus)
async def get_workflow_status(workflow_id: str):
    """
    Get the status of a workflow.
    """
    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow_data = workflows[workflow_id]
    
    return WorkflowStatus(
        workflow_id=workflow_id,
        is_complete=workflow_data.get("is_complete", False),
        current_status=workflow_data.get("current_status", ""),
        steps=workflow_data.get("steps", []),
        results=workflow_data.get("results", []),
        tickets=workflow_data.get("tickets", [])
    )

@app.post("/jira/post-comment")
async def post_jira_comment(request: JiraCommentRequest):
    """
    Post a comment to a JIRA ticket.
    """
    logger.info("Posting comment to JIRA", ticket_id=request.ticket_id)
    
    # In a real implementation, use the JIRA client to post the comment
    # For this mock implementation, we'll simulate the posting
    
    # Simulate some processing time
    await asyncio.sleep(1)
    
    # Return success for mock
    return {"success": True, "message": f"Comment posted to ticket {request.ticket_id}"}

# Helper functions for the workflow
async def run_workflow(workflow_id: str):
    """
    Run the agent workflow and update its status.
    """
    workflow_data = workflows[workflow_id]
    request = workflow_data["request"]
    
    try:
        # Create agent for this workflow
        agent = JiraFeedbackAgent(
            persist_thread=request.get("persist_thread", False),
            user_id=workflow_id
        )
        
        # Update status
        add_workflow_step(
            workflow_id,
            title="Starting Workflow",
            content=f"Starting analysis with JQL: {request['jql']}",
            type="info"
        )
        
        # Allow UI to update - pause for a moment
        await asyncio.sleep(3)
        
        # Get tickets - either from mock items or from JIRA
        tickets = []
        mock_items = request.get("mock_feedback_items", [])
        
        if mock_items:
            add_workflow_step(
                workflow_id,
                title="Using Mock Feedback Items",
                content=f"Using {len(mock_items)} mock feedback items instead of fetching from JIRA",
                type="info"
            )
            
            # Allow UI to update
            await asyncio.sleep(3)
            
            # Convert mock items to JiraTicket objects
            for idx, item in enumerate(mock_items):
                ticket = JiraTicket(
                    id=str(1000 + idx),
                    key=item.get("key", f"MOCK-{idx+1}"),
                    summary=item.get("summary", "Mock feedback"),
                    description=item.get("description", ""),
                    reporter="Mock User",
                    created=time.strftime("%Y-%m-%dT%H:%M:%S.000+0000", time.gmtime()),
                    labels=item.get("labels", ["feedback"])
                )
                tickets.append(ticket)
            
            # Add the mock items as a tool call for visualization
            add_workflow_step(
                workflow_id,
                title="Tool Call: create_mock_feedback",
                content="Creating mock feedback items",
                type="tool_call",
                tool_name="create_mock_feedback",
                args={"count": len(mock_items)},
                result=f"Created {len(mock_items)} mock feedback items"
            )
            
            # Allow UI to update
            await asyncio.sleep(3)
            
        else:
            # Get JIRA tickets
            add_workflow_step(
                workflow_id,
                title="Fetching JIRA Tickets",
                content=f"Fetching tickets using JQL: {request['jql']}",
                type="info"
            )
            
            # Allow UI to update
            await asyncio.sleep(3)
            
            workflow_data["current_status"] = "Fetching JIRA tickets..."
            
            # Get tickets using the JIRA client
            tickets = jira_client.get_feedback_tickets(request["jql"], request["max_results"])
            
            # Add the tool call step
            add_workflow_step(
                workflow_id,
                title="Tool Call: get_jira_feedback",
                content="Called get_jira_feedback to fetch tickets",
                type="tool_call",
                tool_name="get_jira_feedback",
                args={"jql": request["jql"], "max_results": request["max_results"]},
                result=f"Retrieved {len(tickets)} tickets"
            )
            
            # Allow UI to update
            await asyncio.sleep(3)
        
        # Store tickets for display
        workflow_data["tickets"] = [ticket.model_dump() for ticket in tickets]
        
        # Process each ticket using real OpenAI API
        results = []
        
        for i, ticket in enumerate(tickets):
            # Update status
            workflow_data["current_status"] = f"Processing ticket {i+1}/{len(tickets)}: {ticket.key}"
            
            # Add step for processing this ticket
            add_workflow_step(
                workflow_id,
                title=f"Processing Ticket {ticket.key}",
                content=f"Summary: {ticket.summary}",
                type="info"
            )
            
            # Allow UI to update
            await asyncio.sleep(3)
            
            # Add thinking step to show reasoning process
            add_workflow_step(
                workflow_id,
                title="AI Thinking",
                content=f"Analyzing feedback: '{ticket.summary}' to identify user needs and pain points...",
                type="thinking"
            )
            
            # Allow UI to update for thinking step
            await asyncio.sleep(3)
            
            # Create user story using OpenAI
            add_workflow_step(
                workflow_id,
                title="Tool Call: create_user_story",
                content="Converting feedback to user story",
                type="tool_call",
                tool_name="create_user_story",
                args={"summary": ticket.summary, "description": ticket.description or ""},
                result="Processing with OpenAI..."
            )
            
            # Allow UI to update
            await asyncio.sleep(3)
            
            # Simulate processing with OpenAI and add 2.5 second pause
            await asyncio.sleep(2.5)
            
            # Use agent to create user story
            user_story = await agent._create_user_story(
                summary=ticket.summary,
                description=ticket.description or ""
            )
            
            # Update the tool call step with the result
            workflow_data["steps"][-1]["result"] = "User story created successfully"
            
            # Add a success step to show the user story content
            add_workflow_step(
                workflow_id,
                title="User Story Created",
                content=f"Title: {user_story['title']}\n\nDescription: {user_story['description']}\n\nAcceptance Criteria:\n" + 
                        "\n".join([f"- {criterion}" for criterion in user_story['acceptance_criteria']]),
                type="success"
            )
            
            # Allow time for the user to review the user story
            await asyncio.sleep(3)
            
            # Add thinking step for PM response
            add_workflow_step(
                workflow_id,
                title="AI Thinking",
                content=f"Crafting an empathetic product manager response for ticket {ticket.key}...",
                type="thinking"
            )
            
            # Allow UI to update for thinking step
            await asyncio.sleep(3)
            
            # Generate PM response with OpenAI
            add_workflow_step(
                workflow_id,
                title="Tool Call: suggest_pm_response",
                content="Generating PM response",
                type="tool_call",
                tool_name="suggest_pm_response",
                args={"ticket_id": ticket.key, "summary": ticket.summary, "description": ticket.description or ""},
                result="Processing with OpenAI..."
            )
            
            # Allow UI to update
            await asyncio.sleep(3)
            
            # Simulate processing with OpenAI and add 2.5 second pause
            await asyncio.sleep(2.5)
            
            # Use agent to generate PM response
            pm_response = await agent._suggest_pm_response(
                ticket_id=ticket.key,
                summary=ticket.summary,
                description=ticket.description or ""
            )
            
            # Update the tool call step with the result
            workflow_data["steps"][-1]["result"] = "PM response generated successfully"
            
            # Add a success step to show the PM response content
            add_workflow_step(
                workflow_id,
                title="PM Response Created",
                content=pm_response,
                type="success"
            )
            
            # Allow time for the user to review the PM response
            await asyncio.sleep(3)
            
            # Add result
            result = {
                "ticket_id": ticket.key,
                "user_story": user_story,
                "pm_response": pm_response
            }
            
            results.append(result)
            
            # Add a completion step for this ticket
            add_workflow_step(
                workflow_id,
                title=f"Completed Processing Ticket {ticket.key}",
                content=f"Successfully created user story and PM response for '{ticket.summary}'",
                type="info"
            )
            
            # Allow UI to update
            await asyncio.sleep(3)
            
            # Simulate posting to JIRA if requested
            if request["post_to_jira"]:
                add_workflow_step(
                    workflow_id,
                    title="Posting to JIRA",
                    content=f"Posting response to ticket {ticket.key}",
                    type="info"
                )
                
                # Simulate a delay
                await asyncio.sleep(3)
                
                add_workflow_step(
                    workflow_id,
                    title="Posted to JIRA",
                    content=f"Successfully posted response to {ticket.key}",
                    type="success"
                )
                
                # Allow UI to update
                await asyncio.sleep(3)
        
        # Update status
        add_workflow_step(
            workflow_id,
            title="Analysis Complete",
            content=f"Processed {len(tickets)} tickets successfully",
            type="success"
        )
        
        # Set results
        workflow_data["results"] = results
        
        # Mark as complete
        workflow_data["is_complete"] = True
        workflow_data["current_status"] = "Analysis complete"
        
    except Exception as e:
        logger.error("Error in workflow", workflow_id=workflow_id, error=str(e))
        
        # Add error step
        add_workflow_step(
            workflow_id,
            title="Error",
            content=f"An error occurred: {str(e)}",
            type="error"
        )
        
        # Mark as complete with error
        workflow_data["is_complete"] = True
        workflow_data["current_status"] = f"Error: {str(e)}"

def add_workflow_step(workflow_id, title, content, type, tool_name=None, args=None, result=None):
    """Add a step to the workflow."""
    workflow = workflows[workflow_id]
    
    step = {
        "title": title,
        "content": content,
        "type": type,
        "timestamp": time.time()
    }
    
    if type == "tool_call":
        step["tool_name"] = tool_name
        step["args"] = args
        step["result"] = result
    
    workflow["steps"].append(step)
    
    # For debug purposes
    logger.info(f"Workflow step: {title}", workflow_id=workflow_id)

# Import asyncio for async operations
import asyncio

@app.on_event("startup")
async def startup_event():
    """Run when the application starts up."""
    logger.info("Starting JIRA Feedback Analyzer API")

@app.on_event("shutdown")
async def shutdown_event():
    """Run when the application shuts down."""
    logger.info("Shutting down JIRA Feedback Analyzer API")
    
    # Clean up old workflows
    current_time = time.time()
    to_delete = []
    
    for workflow_id, data in workflows.items():
        # Delete workflows older than 1 hour
        if current_time - data.get("timestamp", 0) > 3600:
            to_delete.append(workflow_id)
    
    for workflow_id in to_delete:
        try:
            del workflows[workflow_id]
        except:
            pass

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 