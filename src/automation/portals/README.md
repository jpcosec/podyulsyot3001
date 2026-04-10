# Job Portal Index

This directory contains the portal-specific logic for discovery (scraping), routing, and Ariadne-based automated applications.

## Support Matrix

| Portal | Scrape Status | Apply Status | Search Interaction | Pagination | Deep Crawling |
| :--- | :--- | :--- | :--- | :--- | :--- |
| [**XING**](./xing/README.md) | ✅ Functional | ✅ Map exists | URL Parameters | ❌ No | ✅ Yes |
| [**StepStone**](./stepstone/README.md) | ✅ Functional | ✅ Map exists | URL Parameters | ❌ No | ✅ Yes |
| [**TU Berlin**](./tuberlin/README.md) | ✅ Functional | ❌ Scrape only | URL Parameters | ❌ No | ✅ Yes |
| [**LinkedIn**](./linkedin/README.md) | ❌ N/A | ✅ Map exists | N/A | N/A | N/A |

## Directory Structure

-   `src/automation/portals/<portal>/`:
    -   `routing.py`: Portal-specific application routing (Onsite vs External).
    -   `maps/`: Ariadne Semantic Maps (`easy_apply.json`).
    -   `README.md`: State check and technical details for the portal.

## Global Capabilities

### 1. Search & Filtering
All portals currently use **URL-based filtering**. The system constructs a GET request with query parameters (e.g., `?keywords=...&location=...`). No UI interaction (clicks/typing) is performed during the discovery phase.

### 2. Crawling
-   **Primary Portal**: The system processes the **first page** of results only. Pagination (following "Next" links) is not implemented.
-   **Deep Crawling**: If an external application URL is found (e.g., Greenhouse, Personio), the system **is capable** of crawling that domain to find additional job postings.

---
*For architectural details, see `docs/automation/ariadne_semantics.md`.*
