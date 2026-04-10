# StepStone Portal — State Check

## 1. Discovery (Scrape) State
-   **Status**: ✅ Functional (Last checked: 2026-04-10)
-   **Mechanism**: `StepStoneAdapter` in `src/automation/motors/crawl4ai/portals/stepstone/scrape.py`
-   **Filter Interaction**: URL Parameters only.
-   **Supported Params**:
    -   `job_query`: Keywords for the search.
    -   `city`: Location filter.
    -   `max_days`: Recency filter (mapped to `age_1`, `age_7`, `age_14`, `age_30`).
-   **Crawling**:
    -   **Pagination**: ❌ Not supported.
    -   **Deep Crawling**: ✅ Supported (Cross-portal discovery from external links).

## 2. Application (Ariadne) State
-   **Map Location**: `maps/easy_apply.json`
-   **Verified**: ⚠️ Partially (Path exists, needs live validation).
-   **Auth Strategy**: Persistent Profile.
-   **Routing Logic**: `routing.py` handles `onsite`, `external_url`, and `email` detection.

## Technical Notes
-   **Rescue Robustness**: Includes a title blacklist ("Your connection was interrupted") and a heuristic for company name recovery from the first hero-block bullet.
-   **Location Normalization**: Rejects metadata terms like "Feste Anstellung" from location fields.
