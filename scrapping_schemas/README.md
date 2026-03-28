# 🗂️ Scrapping Schemas Cache

This directory contains the auto-generated JSON schemas used by the `SmartScraperAdapter`. 

When the scraper encounters a job portal for the first time (or if its schema is missing), it uses an LLM (Google Gemini Flash) to learn the page structure and generate optimal CSS selectors that map exactly to the required `JobPosting` Pydantic model. 

These generated selectors are saved here (e.g., `tuberlin_schema.json`) to be reused in future runs. This makes the scraping process robust, lightweight, and significantly faster since it bypasses the LLM on subsequent visits.

**Note:** If a portal changes its UI layout and the CSS selectors break, simply **delete the corresponding schema file** in this folder. The scraper will automatically fall back to using the LLM to learn the new layout on the next run and save a fresh schema here.
