from locust import HttpUser, task, between


class BugTriageLoadTest(HttpUser):
    """
    Simulates concurrent users sending bug reports to the inference API.
    Measures throughput (Requests Per Second) and latency distributions.
    """

    # Simulates user wait time between requests (1 to 3 seconds)
    wait_time = between(1, 3)

    @task
    def predict_endpoint(self):
        """Executes a POST request against the inference endpoint."""
        payload = {
            "issue_title": "Memory leak in background tab",
            "description": "When leaving the dashboard open for 3 hours, Chrome task manager shows memory usage climbing to 4GB. Force killing the tab resolves it.",
            "reported_time": "2026-03-30T10:00:00Z"
        }

        # The 'name' parameter groups the requests in the Locust dashboard
        self.client.post(
            "/api/v1/predict",
            json=payload,
            name="/predict"
        )