# LinkedIn Portal — State Check

## 1. Discovery (Scrape) State
-   **Status**: ❌ Not supported.
-   **Reason**: No scraper implemented. LinkedIn is currently handled as an **apply-only target** where job IDs or URLs are provided externally.

## 2. Application (Ariadne) State
-   **Map Location**: `maps/easy_apply.json`
-   **Verified**: ⚠️ Partially (Path exists, needs live validation).
-   **Auth Strategy**: Persistent Profile.
-   **Routing Logic**: `routing.py` distinguishes between onsite "Easy Apply" and external ATS redirects.

## Technical Notes
-   **Map Design**: The `easy_apply.json` map is designed for the standard LinkedIn application modal.
-   **Routing**: Relies on `application_url` matching `linkedin.com` to determine onsite status.
