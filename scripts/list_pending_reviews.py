"""CLI tool to browse LangGraph jobs and pending reviews."""

import asyncio
import json
import os
import sys
from typing import Optional

# Ensure we can import src
sys.path.append(os.getcwd())

from src.core.api_client import LangGraphAPIClient

async def list_pending():
    client = LangGraphAPIClient()
    print(f"Connecting to LangGraph API at {client.url}...")
    
    try:
        pending = await client.get_pending_reviews()
        
        if not pending:
            print("No pending reviews found.")
            return

        print(f"\nFound {len(pending)} pending review(s):\n")
        print(f"{'Thread ID':<30} | {'Current Node':<20} | {'Status'}")
        print("-" * 70)
        
        for job in pending:
            values = job.get("values", {})
            source = values.get("source", "unknown")
            job_id = values.get("job_id", "unknown")
            print(f"{job['thread_id']:<30} | {str(job['next']):<20} | {job['status']}")
            
    except Exception as e:
        print(f"Error: Could not connect to API or fetch threads. Is 'langgraph dev' running?")
        print(f"Details: {e}")

if __name__ == "__main__":
    asyncio.run(list_pending())
