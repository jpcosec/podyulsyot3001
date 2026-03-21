# Scrapper Phase 1: Robust Scraping and Auto-Apply

## 1. Context
PhD 2.0 needs to scale from 7 to 1,000+ job postings. The current manual approach is blind to JavaScript execution failures and anti-bot measures. Furthermore, the same navigation infrastructure must support automated application (auto-apply) using persistent browser sessions to maintain account logins and bypass manual tasks.

## 2. Objective
Build a 3-layer scraping system (Fallback Cascade) that is:
1. **Deterministic-First:** Extract data using known CSS/XPath selectors to minimize LLM usage.
2. **Auditable:** Generate visual evidence (screenshots) automatically upon failure for easy debugging of JS-intensive sites.
3. **Persistent:** Utilize a dedicated, isolated Chrome profile to maintain sessions for auto-applying with your real account.
4. **Intelligent:** Track deadlines and "stale" status using metadata from JSON artifacts to prioritize applications.

## 3. Don'ts
* **NO LLM Burning:** Do not call the LLM if deterministic selectors successfully extract mandatory fields.
* **NO Profile Sharing:** Never use your primary daily-use Chrome profile; Playwright will crash due to file locks.
* **NO LLM Offsets:** Do not ask the LLM to calculate text offsets; perform deterministic string searching instead.

## 4. Implementation Logic (The Cascade)
1. **Layer 1 (Fast):** `HttpFetcher` + Strategy Selectors. If data is missing or "Access Denied" detected -> Escalate.
2. **Layer 2 (Heavy):** `PlaywrightFetcher` (Stealth mode) + Strategy Selectors. If JS fails to render or selectors fail -> Take screenshot & Escalate.
3. **Layer 3 (AI Fallback):** `GenericAdapter` (LLM). Sends rendered HTML to Gemini to "understand" the new layout.

## 5. Done Definition
- [ ] `PlaywrightFetcher` implements a `try/except` block that saves `error_screenshot.png` on failure.
- [ ] `ScrapingService` implements the full cascade (Deterministic -> Playwright -> LLM).
- [ ] A dedicated "Bot Profile" directory is configured and isolated from the main browser.
- [ ] Automated crawler detects new jobs by comparing IDs and auto-ingests them into `data/jobs/`.
- [ ] API `portfolio/summary` highlights "URGENT" (deadline < 7 days) and "STALE" (scraped > 14 days ago) jobs.

## 6. How to Test
- **JS Failure:** Force a timeout on a heavy site and verify the screenshot is saved in the job folder.
- **Cascade:** Break a selector manually and verify automatic escalation to Layer 3.
- **Persistence:** Verify `run_stepstone_autoapply.py` opens the browser already logged in.
