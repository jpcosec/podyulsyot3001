# Cleanup: Redundant Scraper Package

**Explanation:** The `src/scraper/` package is an architectural remnant. Scraping is functionally a "Discovery Mission" within the automation system. Maintaining a separate package causes duplication of models and confuses the CLI entry point.

**Reference:** 
- `src/scraper/`
- `src/automation/main.py`

**What to fix:** Permanent deletion of the `src/scraper/` package. The `JobPosting` model should be moved to a shared automation contracts file, and the CLI should handle scraping via `automation --task scrape`.

**How to do it:**
1.  Move `JobPosting` model to `src/automation/ariadne/models.py` (or a dedicated DTO module).
2.  `git rm -rf src/scraper/`.
3.  Update any remaining references in `main.py`.

**Depends on:** none
