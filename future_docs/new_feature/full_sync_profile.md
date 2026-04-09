# 🔄 Full Sync Profile

**Deferred:** Implement a `--full-sync` flag in the CLI to force a refresh of the candidate profile from a remote source (via LangGraph API) before running the pipeline.

## Problem Description

The candidate profile is currently loaded from a static local file. There is no mechanism to refresh this profile from a remote source (e.g., Xing or LinkedIn) before a pipeline run.

## Proposed Direction

Implement a `--full-sync` flag that triggers a `Profile.refresh()` call. This refresh will:
1. Use `LangGraphAPIClient` to call a `profile_sync` assistant on the remote server.
2. Fetch the latest raw profile data.
3. Validate and save it to the local `data/reference_data/profile/base_profile/profile_base_data.json` file.

## Design

### `LangGraphAPIClient.get_profile(source: str) -> dict`
- **Intent:** Fetch raw profile data from the remote server.
- **Contract:** Returns a dictionary matching `ProfileBaseData` schema.

### `Profile` Class
- **Intent:** Orchestrate local profile management.
- **Methods:**
    - `load(path: str) -> ProfileBaseData`
    - `save(path: str, data: ProfileBaseData)`
    - `refresh(client: LangGraphAPIClient, source: str)`

## Status

A partial implementation was started (API client updated, CLI flag added), but the task was deferred.

- [x] API Client Update: `get_profile` added to `LangGraphAPIClient` in `src/core/api_client.py`.
- [x] CLI Flag: `--full-sync` added to `pipeline` and `run-batch` in `src/cli/main.py`.
- [ ] Profile Logic: `Profile` class needs implementation in `src/core/profile.py`.
- [ ] Integration: Wire the `refresh` call into the CLI run paths.
