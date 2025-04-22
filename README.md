# Product Feedback Agent

An AI-powered tool that converts customer feedback in JIRA tickets into actionable user stories and PM responses.

## Features

- AI-powered workflow that analyzes feedback and generates structured user stories & PM responses
- Real-time visibility into the AI's thinking process with a step-by-step UI
- Built with FastAPI and the OpenAI API for fast, reliable results
- Prometheus integration for monitoring and metrics collection
- "Enter Mocks with AI" feature to easily test the workflow with realistic data

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/frankmark94/FeedbackAgent.git
   cd FeedbackAgent
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file based on `.env.example` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

1. Start the application:
   ```bash
   python main.py
   ```

2. Open your browser and navigate to http://localhost:8000

3. Enter a JIRA query or use the "Enter Mocks with AI" button to generate sample data

4. Click "Analyze Feedback" to start the agent workflow

## Monitoring

The application includes Prometheus integration for monitoring:

- Endpoint: `/metrics`
- Key metrics:
  - `jira_agent_tickets_processed_total`: Counter for processed tickets
  - `jira_agent_run_duration_seconds`: Histogram for processing duration

## Docker Support

Build and run with Docker:

```bash
docker build -t product-feedback-agent .
docker run -p 8000:8000 -e OPENAI_API_KEY=your_api_key_here product-feedback-agent
```

## License

MIT 