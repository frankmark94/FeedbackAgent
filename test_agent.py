import unittest
from unittest.mock import patch, MagicMock
import json

from agent import JiraFeedbackAgent, FeedbackAnalysisResult
from tools.jira_tools import JiraTicket

class TestJiraFeedbackAgent(unittest.TestCase):
    """Test the JIRA Feedback Agent functionality."""
    
    @patch('agent.Step')
    def test_analyze_feedback(self, mock_step):
        """Test that the agent can analyze feedback tickets."""
        # Mock the step response
        step_instance = MagicMock()
        mock_step.start.return_value = step_instance
        
        # Mock the run method and message response
        step_instance.run.return_value = step_instance
        
        # Set up mock message content with JSON
        mock_response = {
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
        
        # Set the mock message content
        step_instance.messages = [MagicMock(content=json.dumps(mock_response))]
        
        # Create the agent and run analysis
        agent = JiraFeedbackAgent()
        results = agent.analyze_feedback("project = TEST")
        
        # Verify results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].ticket_id, "UX-101")
        self.assertEqual(results[0].user_story["title"], "As a user, I want to easily find the export button")
        self.assertEqual(len(results[0].user_story["acceptance_criteria"]), 3)
        self.assertTrue("Thank you for your feedback" in results[0].pm_response)

if __name__ == "__main__":
    unittest.main() 