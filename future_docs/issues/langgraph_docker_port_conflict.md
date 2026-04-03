# Issue: Conflict between Local LangGraph and Docker Starter Kit

## Context
A conflict occurs when attempting to run LangGraph locally while the n8n `self-hosted-ai-starter-kit` is active. The starter kit includes its own LangGraph/Ollama instances running in Docker, which compete for the same ports (e.g., 8124, 11434).

## Root Cause
- The `self-hosted-ai-starter-kit` (located in `/home/jp/n8n/self-hosted-ai-starter-kit`) starts multiple AI services via Docker Compose.
- Local development commands (like `langgraph dev`) attempt to bind to ports already occupied by the Docker containers.
- Some Docker processes (like `containerd-shim`) run with root privileges, making them harder to identify or stop without checking Docker status.

## Symptoms
- "Address already in use" errors when starting local LangGraph.
- Difficulty identifying the PID because it belongs to a Docker container shim.
- n8n containers restarting automatically due to `unless-stopped` policy.

## Resolution / Prevention
1. **Identify and Stop Docker:** Use `docker compose -f /home/jp/n8n/self-hosted-ai-starter-kit/docker-compose.yml down` before starting local development.
2. **Persistence:** Change n8n restart policy to `no` to prevent it from seizing ports on system startup:
   `docker update --restart=no n8n`
3. **Port Management:** If both must run, reconfigure the local `langgraph.json` or the Docker `.env` file to use non-overlapping ports.
