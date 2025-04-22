import unittest
from fastapi.testclient import TestClient
import json
import time

from main import app

class TestUIIntegration(unittest.TestCase):
    """Test the integration of the UI with the backend workflow."""
    
    def setUp(self):
        self.client = TestClient(app)
    
    def test_ui_loads(self):
        """Test that the UI loads correctly."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("<title>JIRA Feedback Analyzer</title>", response.text)
    
    def test_workflow_api(self):
        """Test the workflow API endpoints."""
        # Start a workflow
        start_response = self.client.post(
            "/workflow/start",
            json={
                "jql": "project = TEST",
                "max_results": 2,
                "persist_thread": False,
                "post_to_jira": False
            }
        )
        
        # Check response
        self.assertEqual(start_response.status_code, 200)
        data = start_response.json()
        self.assertIn("workflow_id", data)
        
        workflow_id = data["workflow_id"]
        
        # Poll for status (max 10 seconds)
        max_polls = 10
        is_complete = False
        
        for _ in range(max_polls):
            status_response = self.client.get(f"/workflow/{workflow_id}/status")
            self.assertEqual(status_response.status_code, 200)
            
            status_data = status_response.json()
            self.assertEqual(status_data["workflow_id"], workflow_id)
            
            # Check if complete
            if status_data["is_complete"]:
                is_complete = True
                break
                
            # Wait before polling again
            time.sleep(1)
        
        self.assertTrue(is_complete, "Workflow did not complete in time")
        
        # Get the final status
        final_status = self.client.get(f"/workflow/{workflow_id}/status").json()
        
        # Verify workflow steps were recorded
        self.assertTrue(len(final_status["steps"]) > 0, "No workflow steps were recorded")
        
        # Verify results
        self.assertTrue(len(final_status["results"]) > 0, "No results were generated")
        
        # Verify first result has expected structure
        first_result = final_status["results"][0]
        self.assertIn("ticket_id", first_result)
        self.assertIn("user_story", first_result)
        self.assertIn("pm_response", first_result)
        
        # Verify user story format
        user_story = first_result["user_story"]
        self.assertIn("title", user_story)
        self.assertIn("description", user_story)
        self.assertIn("acceptance_criteria", user_story)
        self.assertTrue(len(user_story["acceptance_criteria"]) > 0)

if __name__ == "__main__":
    unittest.main() 