"""LangGraph API client for thread discovery and state management.

Provides a simplified interface over the langgraph-sdk to handle pipeline
persistence, metadata extraction, and remote state resumption.
"""

from __future__ import annotations

import logging
import os
import re
import signal
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from langgraph_sdk import get_client

from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


def _next_review_node(next_nodes: list[str] | None) -> str | None:
    """Return the active HITL node name for generate_documents_v2, if any."""
    if not next_nodes:
        return None
    for node in next_nodes:
        if node.startswith("hitl_") or node in {
            "stage_2_semantic_bridge",
            "stage_3_macroplanning",
            "stage_5_assembly_render",
        }:
            return node
    return None


def _derive_thread_status(state: dict[str, Any]) -> str:
    """Derive a stable run status from thread state."""
    if _next_review_node(state.get("next", [])) is not None:
        return "pending_review"

    values = state.get("values", {})
    error_state = values.get("error_state")
    if error_state:
        return "failed"

    return values.get("status", "unknown")


def _normalize_run_result(
    result: dict[str, Any] | None,
    state: dict[str, Any],
    *,
    error: str | None = None,
) -> dict[str, Any]:
    """Normalize LangGraph run/join output into a UI-friendly result."""
    normalized = dict(result or {})
    normalized["status"] = _derive_thread_status(state)

    values = state.get("values", {})
    if error:
        normalized["error"] = error
    elif values.get("error_state"):
        normalized["error"] = values["error_state"].get("message")

    if state.get("next"):
        normalized["next"] = state["next"]

    return normalized


class LangGraphConnectionError(Exception):
    """Raised when the LangGraph API is unreachable or returns invalid responses."""

    pass


class LangGraphAPIClient:
    """Interacts with the LangGraph API to manage and query job application threads.

    This client abstracts the underlying SDK and provides robust autodetection
    for the API port by scanning running processes and common ports.
    """

    DEFAULT_PORT = 8124

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
        """Attempt to find where the LangGraph API is running."""
        # 1. Env Var (User explicit)
        explicit = os.getenv("LANGGRAPH_API_URL")
        if explicit:
            return explicit

        # 2. Try default port (Health Check)
        url = f"http://localhost:{self.DEFAULT_PORT}"
        try:
            with httpx.Client(timeout=0.5) as client:
                resp = client.get(f"{url}/ok")
                if resp.status_code == 200:
                    return url
        except Exception:
            pass

        # 3. Scan processes for 'langgraph dev'
        try:
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
                            return url
                except Exception:
                    pass
        except Exception:
            pass

        return f"http://localhost:{self.DEFAULT_PORT}"

    @classmethod
    def ensure_server(
        cls,
        *,
        port: int = 8124,
        timeout_seconds: float = 60.0,
        log_file: str | Path = "logs/langgraph_api.log",
    ) -> str:
        """Ensure a LangGraph API server is reachable."""
        url = f"http://localhost:{port}"

        # Check if already healthy
        try:
            with httpx.Client(timeout=1.0) as client:
                resp = client.get(f"{url}/ok")
                if resp.status_code == 200:
                    os.environ["LANGGRAPH_API_URL"] = url
                    return url
        except Exception:
            pass

        cls._kill_stale_dev_server(port)

        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join(
            [p for p in [env.get("PYTHONPATH", ""), os.getcwd()] if p]
        )

        logger.info(
            "%s Starting LangGraph dev server on port %s...",
            LogTag.FAST,
            port,
        )

        with log_path.open("wb") as stream:
            subprocess.Popen(
                [
                    "langgraph",
                    "dev",
                    "--config",
                    "langgraph.json",
                    "--no-browser",
                    "--port",
                    str(port),
                ],
                stdout=stream,
                stderr=subprocess.STDOUT,
                env=env,
                start_new_session=True,
            )

        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            try:
                with httpx.Client(timeout=1.0) as client:
                    resp = client.get(f"{url}/ok")
                    if resp.status_code == 200:
                        # Server is up, wait a bit more for graphs to load
                        time.sleep(2.0)
                        os.environ["LANGGRAPH_API_URL"] = url
                        logger.info("%s LangGraph API ready at %s", LogTag.OK, url)
                        return url
            except Exception:
                pass
            time.sleep(1.0)

        raise LangGraphConnectionError(
            f"Timed out waiting for LangGraph API at {url}. Check {log_file} for details."
        )

    @staticmethod
    def _kill_stale_dev_server(port: int) -> None:
        try:
            output = subprocess.check_output(["lsof", f"-ti:{port}"], text=True).strip()
        except Exception:
            return

        if not output:
            return

        for line in output.splitlines():
            try:
                pid = int(line.strip())
            except ValueError:
                continue
            try:
                os.kill(pid, signal.SIGKILL)  # Be more aggressive
                logger.warning(
                    "%s Terminated stale LangGraph process on port %s (pid=%s)",
                    LogTag.WARN,
                    port,
                    pid,
                )
            except (ProcessLookupError, PermissionError):
                continue

    def is_healthy(self) -> bool:
        """Check whether the LangGraph API health endpoint responds successfully."""
        try:
            with httpx.Client(timeout=1.0) as client:
                resp = client.get(f"{self.url}/ok")
                return resp.status_code == 200
        except Exception:
            return False

    @staticmethod
    def thread_id_for(source: str, job_id: str) -> str:
        """Return the deterministic LangGraph thread UUID for one job."""
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"postulator:{source}:{job_id}"))

    async def list_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List and enrich all threads managed by the API."""
        try:
            threads = await self.client.threads.search(limit=limit)
            enriched_threads = []
            for thread in threads:
                try:
                    state = await self.client.threads.get_state(
                        thread["thread_id"], subgraphs=True
                    )
                    values = state.get("values", {})
                    has_review_pending = (
                        _next_review_node(state.get("next", [])) is not None
                    )
                    enriched_threads.append(
                        {
                            **thread,
                            "state": state,
                            "source": values.get("source", "unknown"),
                            "job_id": values.get("job_id", "unknown"),
                            "status": (
                                "pending_review"
                                if has_review_pending
                                else values.get("status", "unknown")
                            ),
                            "location": values.get("location")
                            or values.get("city")
                            or "N/A",
                            "updated_at": thread.get("updated_at")
                            or thread.get("created_at")
                            or "N/A",
                            "current_node": values.get("current_node", "N/A"),
                            "has_review_pending": has_review_pending,
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
        try:
            threads = await self.list_jobs()
            pending = []
            for thread in threads:
                state = thread.get("state", {})
                review_node = _next_review_node(state.get("next", []))
                if review_node:
                    pending.append(
                        {
                            "thread_id": thread["thread_id"],
                            "status": "pending_review",
                            "values": state.get("values", {}),
                            "next": state["next"],
                            "review_node": review_node,
                        }
                    )
            return pending
        except Exception as e:
            logger.error(f"  [❌] Error fetching pending reviews: {e}")
            return []

    async def get_thread_metadata(self, thread_id: str) -> Dict[str, Any]:
        """Extract rich metadata from a thread state for UI display."""
        try:
            state = await self.client.threads.get_state(thread_id, subgraphs=True)
            values = state.get("values", {})
            return {
                "source": values.get("source", "unknown"),
                "job_id": values.get("job_id", "unknown"),
                "status": values.get("status", "unknown"),
                "city": values.get("city") or values.get("location") or "N/A",
                "next_nodes": state.get("next", []),
                "last_node": values.get("current_node", "N/A"),
                "has_review_pending": _next_review_node(state.get("next", []))
                is not None,
            }
        except Exception:
            return {}

    async def resume_thread(
        self,
        thread_id: str,
        payload: Dict[str, Any],
        node_name: str | None = None,
    ) -> Dict[str, Any]:
        """Update thread state and resume execution."""
        try:
            state = await self.client.threads.get_state(thread_id, subgraphs=True)
            assistant_id = state.get("metadata", {}).get(
                "graph_id", "generate_documents_v2"
            )
            resolved_node = node_name or _next_review_node(state.get("next", []))
            if not resolved_node:
                raise ValueError(f"No pending review node found for thread {thread_id}")
            logger.info(
                f"  [🚀] Resuming thread {thread_id} at node {resolved_node}..."
            )
            checkpoint = state.get("checkpoint")
            checkpoint_id = state.get("checkpoint_id")
            await self.client.threads.update_state(
                thread_id,
                payload,
                as_node=resolved_node,
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
            latest_state = await self.client.threads.get_state(
                thread_id, subgraphs=True
            )
            logger.info(f"  [✅] Thread {thread_id} resumed successfully.")
            return _normalize_run_result(result, latest_state)
        except Exception as e:
            logger.error(f"  [❌] Failed to resume thread {thread_id}: {e}")
            try:
                state = await self.client.threads.get_state(thread_id, subgraphs=True)
            except Exception:
                raise
            return _normalize_run_result({}, state, error=str(e))

    async def invoke_assistant(
        self,
        assistant_id: str,
        source: str,
        job_id: str,
        source_url: Optional[str] = None,
        initial_input: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Start a new assistant run for a specific job thread."""
        thread_id = self.thread_id_for(source, job_id)
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
        try:
            result = await self.client.runs.join(thread_id, run["run_id"])
        except Exception as exc:
            state = await self.client.threads.get_state(thread_id, subgraphs=True)
            return _normalize_run_result({}, state, error=str(exc))

        state = await self.client.threads.get_state(thread_id, subgraphs=True)
        return _normalize_run_result(result, state)

    async def invoke_pipeline(
        self,
        source: str,
        job_id: str,
        source_url: Optional[str] = None,
        initial_input: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Start a new pipeline run for a specific job."""
        return await self.invoke_assistant(
            "generate_documents_v2",
            source=source,
            job_id=job_id,
            source_url=source_url,
            initial_input=initial_input,
        )
