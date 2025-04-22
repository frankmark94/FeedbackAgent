# JIRA Feedback Analyzer

An AI-powered agent that fetches feedback tickets from JIRA, analyzes them, and generates user stories with PM responses using the OpenAI Agents SDK.

## Features

- Connect to JIRA Cloud via API to fetch feedback tickets
- Process tickets with an OpenAI Agent to extract valuable insights
- Generate structured user stories with acceptance criteria
- Create empathetic PM responses for feedback
- Expose functionality through a FastAPI REST API
- Metrics and health monitoring
- Interactive UI for visualizing agent workflow and results

## Setup

### Prerequisites

- Python 3.9+
- JIRA Cloud instance with API access
- OpenAI API key

### Environment Variables

Copy the `.env.example` file to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Then edit the `.env` file with your actual credentials:

```
OPENAI_API_KEY=your_openai_api_key
JIRA_API_TOKEN=your_jira_api_token
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_PROJECT_KEY=PROJECT
JIRA_USER_EMAIL=your_email@example.com
```

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/jira-feedback-agent.git
cd jira-feedback-agent
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Running the Application

Start the API server:

```bash
python main.py
```

The server will be available at http://localhost:8000.

### Using the Web UI

1. Open your browser and go to http://localhost:8000/
2. Enter your JIRA Query (JQL) in the form
3. Set the maximum number of results to process
4. Check "Persist Thread" if you want to maintain agent context across runs
5. Check "Post Results to JIRA" if you want to automatically post PM responses as comments
6. Click "Analyze Feedback" to start the analysis

The UI will show:

- Real-time visualization of the agent workflow with each step recorded
- Tool calls with input arguments and results
- Final results with user stories and PM responses
- Options to view tickets in JIRA or post responses as comments

### API Endpoints

#### POST /analyze-feedback

Analyze JIRA feedback tickets and generate user stories.

**Request Body:**

```json
{
  "jql": "project = UX AND labels = feedback AND created >= -7d",
  "max_results": 10
}
```

**Query Parameters:**

- `persist_thread` (boolean, optional): Reuse the same agent thread across requests for context
- `user_id` (string, optional): User identifier for personalization

**Response:**

```json
{
  "results": [
    {
      "ticket_id": "UX-101",
      "user_story": {
        "title": "As a user, I want to easily find the export button",
        "description": "The export button should be prominently placed so users can quickly export their data without frustration.",
        "acceptance_criteria": [
          "Export button is visible in the main toolbar",
          "Export button has appropriate icon and label",
          "Hovering over the button shows a tooltip with export options"
        ]
      },
      "pm_response": "Thank you for your feedback about the export button location. We agree it should be more prominent. We'll be moving it to the main toolbar in our next UI update scheduled for next month."
    }
  ]
}
```

#### POST /workflow/start

Start a new agent workflow with detailed tracking.

**Request Body:**

```json
{
  "jql": "project = UX AND labels = feedback",
  "max_results": 3,
  "persist_thread": false,
  "post_to_jira": false
}
```

**Response:**

```json
{
  "workflow_id": "12345-uuid-67890"
}
```

#### GET /workflow/{workflow_id}/status

Get the status of an ongoing or completed workflow.

**Response:**

```json
{
  "workflow_id": "12345-uuid-67890",
  "is_complete": true,
  "current_status": "Analysis complete",
  "steps": [
    {
      "title": "Starting Workflow",
      "content": "Starting analysis with JQL: project = UX",
      "type": "info",
      "timestamp": 1637012345.678
    },
    {
      "title": "Tool Call: get_jira_feedback",
      "content": "Called get_jira_feedback to fetch tickets",
      "type": "tool_call",
      "tool_name": "get_jira_feedback",
      "args": {"jql": "project = UX", "max_results": 3},
      "result": "Retrieved 3 tickets",
      "timestamp": 1637012346.789
    }
    // ... more steps
  ],
  "results": [
    // analysis results like the /analyze-feedback endpoint
  ],
  "tickets": [
    // original ticket data
  ]
}
```

#### GET /health

Health check endpoint.

#### GET /metrics

Prometheus metrics endpoint.

### Example cURL Request

```bash
curl -X POST "http://localhost:8000/analyze-feedback" \
  -H "Content-Type: application/json" \
  -d '{"jql": "project = UX AND labels = feedback AND created >= -7d", "max_results": 5}'
```

## Docker

### Building the Docker Image

```bash
docker build -t jira-feedback-agent .
```

### Running the Container

```bash
docker run -p 8000:8000 --env-file .env jira-feedback-agent
```

## Development

### Running Tests

Run all tests:

```bash
python -m unittest discover
```

Run UI integration tests:

```bash
python test_ui_integration.py
```

### Mock Mode

If JIRA credentials are not provided, the application will run in mock mode, using sample data for testing.

## License

[MIT License](LICENSE) 