"""LangGraph API client for thread discovery and state management.

Provides a simplified interface over the langgraph-sdk to handle pipeline
persistence, metadata extraction, and remote state resumption.
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from langgraph_sdk import get_client

from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


class LangGraphConnectionError(Exception):
    """Raised when the LangGraph API is unreachable or returns invalid responses."""

    pass


class LangGraphAPIClient:
    """Interacts with the LangGraph API to manage and query job application threads.

    This client abstracts the underlying SDK and provides robust autodetection
    for the API port by scanning running processes and common ports.
    """

    def __init__(self, url: Optional[str] = None):
        """Initialize the client, attempting autodetection if no URL is provided.

        Args:
            url: Explicit API URL. If None, checks LANGGRAPH_API_URL or scans ports.
        """
        self.url = url or self._detect_url()
        try:
            logger.info(f"{LogTag.OK} Initializing LangGraph client at {self.url}")
            self.client = get_client(url=self.url)
        except Exception as e:
            logger.error(
                f"{LogTag.FAIL} Failed to initialize LangGraph SDK client: {e}"
            )
            raise LangGraphConnectionError(f"Could not connect to {self.url}") from e

    def _detect_url(self) -> str:
        """Attempt to find where the LangGraph API is running.

        Checks environment variables, scans running processes for 'langgraph dev',
        and probes common ports (8124, 8123, 8125).

        Returns:
            The detected API base URL.
        """
        # 1. Env Var (User explicit)
        explicit = os.getenv("LANGGRAPH_API_URL")
        if explicit:
            return explicit

        # 2. Scan processes for 'langgraph dev'
        try:
            # Look for langgraph dev --port XXXX
            cmd = "ps aux | grep 'langgraph dev' | grep -v grep"
            output = subprocess.check_output(cmd, shell=True).decode()
            match = re.search(r"--port\s+(\d+)", output)
            if match:
                port = match.group(1)
                url = f"http://localhost:{port}"
                try:
                    with httpx.Client(timeout=0.5) as client:
                        resp = client.get(f"{url}/ok")
                        if resp.status_code == 200:
                            logger.info(
                                f"{LogTag.FAST} Autodetected LangGraph API on port {port} via process scan."
                            )
                            return url
                except Exception:
                    pass
        except Exception:
            pass

        # 3. Try common ports (Health Check)
        common_ports = [8124, 8123, 8125]
        for port in common_ports:
            url = f"http://localhost:{port}"
            try:
                # Use httpx for a quick check
                with httpx.Client(timeout=0.5) as client:
                    resp = client.get(f"{url}/ok")
                    if resp.status_code == 200:
                        logger.info(
                            f"{LogTag.OK} Found active LangGraph API on port {port}."
                        )
                        return url
            except Exception:
                continue

        # Default fallback
        return "http://localhost:8124"

    @classmethod
    def ensure_server(
        cls,
        *,
        port: int = 8124,
        timeout_seconds: float = 15.0,
        log_file: str | Path = "logs/langgraph_api.log",
    ) -> str:
        """Ensure a LangGraph API server is reachable.

        Starts `langgraph dev` if necessary and returns the active base URL.
        """
        candidate = cls()
        if candidate.is_healthy():
            return candidate.url

        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join(
            [p for p in [env.get("PYTHONPATH", ""), os.getcwd()] if p]
        )
        logger.info(
            "%s LangGraph API not reachable. Starting dev server on port %s",
            LogTag.FAST,
            port,
        )
        with log_path.open("ab") as stream:
            subprocess.Popen(
                ["langgraph", "dev", "--port", str(port)],
                stdout=stream,
                stderr=subprocess.STDOUT,
                env=env,
                start_new_session=True,
            )

        url = f"http://localhost:{port}"
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            try:
                with httpx.Client(timeout=1.0) as client:
                    resp = client.get(f"{url}/ok")
                    if resp.status_code == 200:
                        os.environ["LANGGRAPH_API_URL"] = url
                        logger.info("%s LangGraph API ready at %s", LogTag.OK, url)
                        return url
            except Exception:
                time.sleep(0.5)

        raise LangGraphConnectionError(f"Timed out waiting for LangGraph API at {url}")

    def is_healthy(self) -> bool:
        try:
            with httpx.Client(timeout=1.0) as client:
                resp = client.get(f"{self.url}/ok")
                return resp.status_code == 200
        except Exception:
            return False

    async def list_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List and enrich all threads managed by the API.

        Queries the API for all threads and extracts their latest state metadata.

        Args:
            limit: Maximum number of threads to return.

        Returns:
             List of thread state dictionaries.
        """
        try:
            threads = await self.client.threads.search(limit=limit)
            enriched_threads = []
            for thread in threads:
                try:
                    state = await self.client.threads.get_state(thread["thread_id"])
                    values = state.get("values", {})
                    enriched_threads.append(
                        {
                            **thread,
                            "state": state,
                            "source": values.get("source", "unknown"),
                            "job_id": values.get("job_id", "unknown"),
                            "status": values.get("status", "unknown"),
                            "location": values.get("location")
                            or values.get("city")
                            or "N/A",
                            "updated_at": thread.get("updated_at")
                            or thread.get("created_at")
                            or "N/A",
                            "current_node": values.get("current_node", "N/A"),
                            "has_review_pending": "human_review_node"
                            in state.get("next", []),
                        }
                    )
                except Exception:
                    enriched_threads.append({**thread, "state": {}})
            return enriched_threads
        except Exception as e:
            logger.error(f"  [❌] Failed to search threads: {e}")
            raise LangGraphConnectionError(str(e))

    async def get_pending_reviews(self) -> List[Dict[str, Any]]:
        """List jobs that are currently at a human review breakpoint."""
        logger.info(f"  [🔗] Fetching pending reviews from {self.url}...")
        try:
            threads = await self.list_jobs()
            pending = []
            for thread in threads:
                state = thread.get("state", {})
                if state.get("next") and "human_review_node" in state["next"]:
                    pending.append(
                        {
                            "thread_id": thread["thread_id"],
                            "status": "pending_review",
                            "values": state.get("values", {}),
                            "next": state["next"],
                        }
                    )
            return pending
        except Exception as e:
            logger.error(f"  [❌] Error fetching pending reviews: {e}")
            return []

    async def get_thread_metadata(self, thread_id: str) -> Dict[str, Any]:
        """Extract rich metadata from a thread state for UI display."""
        try:
            state = await self.client.threads.get_state(thread_id)
            values = state.get("values", {})
            return {
                "source": values.get("source", "unknown"),
                "job_id": values.get("job_id", "unknown"),
                "status": values.get("status", "unknown"),
                "city": values.get("city") or values.get("location") or "N/A",
                "next_nodes": state.get("next", []),
                "last_node": values.get("current_node", "N/A"),
                "has_review_pending": "human_review_node" in state.get("next", []),
            }
        except Exception:
            return {}

    async def resume_thread(
        self,
        thread_id: str,
        payload: Dict[str, Any],
        node_name: str = "human_review_node",
    ) -> Dict[str, Any]:
        """Update thread state and resume execution."""
        logger.info(f"  [🚀] Resuming thread {thread_id} at node {node_name}...")
        try:
            state = await self.client.threads.get_state(thread_id, subgraphs=True)
            assistant_id = state.get("metadata", {}).get("graph_id", "pipeline")
            checkpoint = state.get("checkpoint")
            checkpoint_id = state.get("checkpoint_id")
            await self.client.threads.update_state(
                thread_id,
                payload,
                as_node=node_name,
                checkpoint=checkpoint,
                checkpoint_id=checkpoint_id,
            )
            run = await self.client.runs.create(
                thread_id,
                assistant_id=assistant_id,
                input=None,
                checkpoint=checkpoint,
                checkpoint_id=checkpoint_id,
            )
            result = await self.client.runs.join(thread_id, run["run_id"])
            logger.info(f"  [✅] Thread {thread_id} resumed successfully.")
            return result
        except Exception as e:
            logger.error(f"  [❌] Failed to resume thread {thread_id}: {e}")
            raise

    async def invoke_assistant(
        self,
        assistant_id: str,
        source: str,
        job_id: str,
        source_url: Optional[str] = None,
        initial_input: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Start a new assistant run for a specific job thread."""
        thread_id = f"{source}_{job_id}"
        logger.info(f"  [⚡] Invoking {assistant_id} for {source}/{job_id}...")
        payload = {
            "source": source,
            "job_id": job_id,
            "source_url": source_url,
            "status": "pending",
        }
        if initial_input:
            payload.update(initial_input)
        try:
            await self.client.threads.create(thread_id=thread_id)
        except Exception as exc:
            if "already exists" not in str(exc).lower():
                raise

        run = await self.client.runs.create(
            thread_id,
            assistant_id=assistant_id,
            input=payload,
        )
        return await self.client.runs.join(thread_id, run["run_id"])

    async def invoke_pipeline(
        self,
        source: str,
        job_id: str,
        source_url: Optional[str] = None,
        initial_input: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Start a new pipeline run for a specific job."""
        return await self.invoke_assistant(
            "pipeline",
            source=source,
            job_id=job_id,
            source_url=source_url,
            initial_input=initial_input,
        )
