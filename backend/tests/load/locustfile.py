from __future__ import annotations

import os
import uuid

from locust import HttpUser, between, tag, task


class AuthenticatedAPIUser(HttpUser):
    abstract = True
    wait_time = between(0.5, 2.0)

    def on_start(self) -> None:
        response = self.client.post(
            "/api/v1/auth/token/",
            json={
                "username": os.environ.get("LOAD_TEST_USERNAME", "loadtest"),
                "password": os.environ.get("LOAD_TEST_PASSWORD", ""),
            },
            name="/api/v1/auth/token/",
        )
        if response.status_code != 200:
            raise RuntimeError("Load-test authentication failed")
        self.client.headers["Authorization"] = f"Bearer {response.json()['access']}"


class ResearchReadUser(AuthenticatedAPIUser):
    weight = 4

    @tag("read")
    @task(5)
    def list_analyses(self) -> None:
        with self.client.get(
            "/api/v1/analysis/?page_size=25&ordering=-created_at",
            name="/api/v1/analysis/",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Unexpected response: {response.status_code}")

    @tag("read")
    @task(1)
    def list_catalysts(self) -> None:
        self.client.get(
            "/api/v1/catalysts/?is_active=true&page_size=25",
            name="/api/v1/catalysts/",
        )


class ConcurrentAnalysisUser(AuthenticatedAPIUser):
    weight = 1

    @tag("analysis")
    @task
    def submit_analysis(self) -> None:
        symbol = os.environ.get("LOAD_TEST_SYMBOL", "AAPL")
        self.client.post(
            "/api/v1/analysis/",
            json={
                "symbol": symbol,
                "exchange": os.environ.get("LOAD_TEST_EXCHANGE", "US"),
                "scope": "single",
                "config": {},
            },
            headers={"Idempotency-Key": f"load-{uuid.uuid4()}"},
            name="/api/v1/analysis/",
        )
