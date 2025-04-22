import time
import structlog
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Configure structlog
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
)

logger = structlog.get_logger()

# Prometheus metrics
TICKETS_PROCESSED = Counter(
    "jira_agent_tickets_processed_total",
    "Total number of JIRA tickets processed"
)

RUN_DURATION = Histogram(
    "jira_agent_run_duration_seconds",
    "Duration of agent runs in seconds",
    buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 120.0]
)

class Timer:
    """Context manager for timing operations and recording to Prometheus."""
    
    def __init__(self, metric=None):
        self.metric = metric
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        if self.metric:
            self.metric.observe(duration)
        return False  # Don't suppress exceptions
            
def get_metrics():
    """Generate latest Prometheus metrics."""
    return generate_latest()

# Health check
def health_check():
    """Return a health check response."""
    return {"status": "ok"} 