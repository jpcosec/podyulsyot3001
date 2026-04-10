# XING Portal — State Check

## 1. Discovery (Scrape) State
-   **Status**: ✅ Functional (Last checked: 2026-04-10)
-   **Mechanism**: `XingAdapter` in `src/automation/motors/crawl4ai/portals/xing/scrape.py`
-   **Filter Interaction**: URL Parameters only.
-   **Supported Params**:
    -   `job_query`: Keywords for the search.
    -   `city`: Location filter.
    -   `max_days`: Recency filter (mapped to 1, 7, 14, 30 days).
-   **Crawling**:
    -   **Pagination**: ❌ Not supported.
    -   **Deep Crawling**: ✅ Supported (Cross-portal discovery from external links).

## 2. Application (Ariadne) State
-   **Map Location**: `maps/easy_apply.json`
-   **Verified**: ⚠️ Partially (Path exists, needs live validation).
-   **Auth Strategy**: Persistent Profile.
-   **Routing Logic**: `routing.py` handles `onsite`, `external_url`, and `email` detection.

## Technical Notes
-   **Listing Extraction**: Uses BeautifulSoup4 to parse structured `listing_texts` from search result cards.
-   **Normalization**: Relies on `src/automation/ariadne/job_normalization.py` for XING-specific heading recovery (e.g., "Deine Rolle", "Qualifikation").
