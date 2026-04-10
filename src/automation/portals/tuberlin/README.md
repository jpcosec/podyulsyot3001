# TU Berlin Portal — State Check

## 1. Discovery (Scrape) State
-   **Status**: ✅ Functional (Last checked: 2026-04-10)
-   **Mechanism**: `TUBerlinAdapter` in `src/automation/motors/crawl4ai/portals/tuberlin/scrape.py`
-   **Filter Interaction**: URL Parameters only.
-   **Supported Params**:
    -   `job_query`: Keywords for the search.
    -   `categories`: List of work-type filters (e.g., `wiss-mlehr`, `besch-itb`).
-   **Crawling**:
    -   **Pagination**: ❌ Not supported.
    -   **Deep Crawling**: ✅ Supported (Cross-portal discovery from external links).

## 2. Application (Ariadne) State
-   **Status**: ❌ Not supported.
-   **Reason**: TU Berlin (Stellenticket) is currently a **scrape-only target**. Applications usually involve external PDF-based processes or faculty-specific forms that are not yet mapped in Ariadne.

## Technical Notes
-   **Company Discovery**: Attempts to seed discovery from Stellenticket PDF URLs, though these are often guarded by anti-bot measures.
-   **Normalization**: Standardizes company name to "Technische Universität Berlin" or faculty derivatives.
