"""Smart Scraper Adapter — Enterprise-grade job extraction orchestrator.

Replaces the legacy BaseScraperAdapter with:
1. **Concurrent crawling** via ``arun_many`` + ``SemaphoreDispatcher`` + ``RateLimiter``
2. **Anti-bot stealth** via ``simulate_user``, ``magic``, ``override_navigator``
3. **Text-mode optimization** via ``text_mode=True`` + ``excluded_tags``
4. **LLM-first schema generation** with CSS caching for production speed
5. **Pydantic validation** with LLM rescue fallback
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Tuple
from pathlib import Path
from pydantic import ValidationError
from dotenv import load_dotenv

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
    LLMConfig,
    SemaphoreDispatcher,
    RateLimiter,
)
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy, LLMExtractionStrategy
from .models import JobPosting

# Load .env for API keys
load_dotenv()

logger = logging.getLogger(__name__)


class SmartScraperAdapter(ABC):
    """Abstract base class for all job portal scrapers.

    Subclasses must implement:
    - ``source_name``: folder name under ``data/source/``
    - ``supported_params``: list of CLI params the portal understands
    - ``get_search_url(**kwargs)``: build the listing URL
    - ``extract_job_id(url)``: extract numeric ID from a job URL
    - ``extract_links(crawl_result)``: discover job links from listing page
    - ``get_llm_instructions()``: portal-specific hints for the LLM rescue
    """

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def source_name(self) -> str:
        pass

    @property
    @abstractmethod
    def supported_params(self) -> List[str]:
        pass

    @abstractmethod
    def get_search_url(self, **kwargs) -> str:
        pass

    @abstractmethod
    def extract_job_id(self, url: str) -> str:
        pass

    @abstractmethod
    def extract_links(self, crawl_result: Any) -> List[str]:
        pass

    @abstractmethod
    def get_llm_instructions(self) -> str:
        pass

    # ------------------------------------------------------------------
    # LLM configuration (Gemini Flash by default)
    # ------------------------------------------------------------------

    def get_llm_config(self) -> LLMConfig:
        """Centralized LLM config using Google Gemini Flash (fast + cheap)."""
        return LLMConfig(
            provider="gemini/gemini-2.5-flash",
            api_token=os.environ.get("GOOGLE_API_KEY", ""),
            temperature=0.1,
        )

    def _has_llm_key(self) -> bool:
        """Check if the required API key is available."""
        return bool(os.environ.get("GOOGLE_API_KEY"))

    # ------------------------------------------------------------------
    # Anti-bot and performance configs
    # ------------------------------------------------------------------

    def get_browser_config(self) -> BrowserConfig:
        """Lightweight browser: headless + text-only (no images/media)."""
        return BrowserConfig(
            headless=True,
            text_mode=True,
        )

    def get_base_crawl_config(self) -> CrawlerRunConfig:
        """Base config with anti-bot stealth and content optimization."""
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            # Anti-Bot (Stealth Mode)
            simulate_user=True,
            magic=True,
            override_navigator=True,
            # Content optimization (less noise → fewer tokens → cheaper LLM)
            word_count_threshold=10,
            exclude_external_images=True,
            exclude_external_links=False,  # <--- Fixed (vital for StepStone)
            excluded_tags=["nav", "footer", "script", "style", "aside"],
        )

    def get_dispatcher(self) -> SemaphoreDispatcher:
        """Concurrent dispatcher with human-like rate limiting."""
        return SemaphoreDispatcher(
            max_session_permit=5,
            rate_limiter=RateLimiter(
                base_delay=(1.0, 3.0),
                max_retries=2,
                rate_limit_codes=[429, 503],
            ),
        )

    # ------------------------------------------------------------------
    # Schema caching
    # ------------------------------------------------------------------

    @property
    def schema_cache_path(self) -> Path:
        return Path(f"./schemas/{self.source_name}_schema.json")

    async def get_fast_schema(
        self, crawler: AsyncWebCrawler, sample_url: str
    ) -> Optional[dict]:
        """Return cached CSS schema or auto-generate it using LLM."""
        if self.schema_cache_path.exists():
            logger.info("  [📦] Using cached CSS schema.")
            return json.loads(self.schema_cache_path.read_text())

        if not self._has_llm_key():
            logger.warning("  [⚠️] No API key. Skipping CSS schema generation.")
            return None

        logger.info("  [🧠] Learning page structure for the first time...")

        sample_result = await crawler.arun(
            url=sample_url, config=self.get_base_crawl_config()
        )

        if not sample_result.success:
            logger.error("  [❌] Could not download sample page.")
            return None

        try:
            # We pass the exact mold that Pydantic needs to fill
            molde_json = json.dumps(JobPosting.model_json_schema(), indent=2)
            
            esquema = JsonCssExtractionStrategy.generate_schema(
                html=sample_result.cleaned_html[:50000],
                schema_type="CSS",
                target_json_example=molde_json,
                query=f"Generate CSS selectors to extract job postings from {self.source_name} mapping exactly to the required fields in the JSON.",
                llm_config=self.get_llm_config(),
            )
            self.schema_cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.schema_cache_path.write_text(
                json.dumps(esquema, indent=2, ensure_ascii=False)
            )
            logger.info("  [✅] CSS schema generated and cached.")
            return esquema
        except Exception as e:
            logger.error(f"  [❌] Error generating schema: {e}")
            return None

    # ------------------------------------------------------------------
    # Validation helper
    # ------------------------------------------------------------------

    def _try_validate(self, raw_content: str) -> Tuple[Optional[dict], Optional[str]]:
        """Try to parse JSON and validate against JobPosting schema."""
        try:
            raw_data = json.loads(raw_content)
            raw_data = (
                raw_data[0]
                if isinstance(raw_data, list) and raw_data
                else raw_data
            )
            if isinstance(raw_data, dict):
                return JobPosting(**raw_data).model_dump(), None
            return None, "Extracted content is not a valid JSON dictionary."
        except Exception as e:
            return None, str(e)

    async def _llm_rescue(
        self, markdown_content: str
    ) -> Tuple[Optional[dict], Optional[str]]:
        """Use LLM to extract structured data from markdown content.

        Calls litellm directly instead of going through crawl4ai's arun,
        which fails on ``raw://`` URLs containing markdown brackets.
        """
        if not self._has_llm_key() or not markdown_content:
            return None, "No LLM API key or empty markdown content."

        logger.info("  [🤖] LLM Rescue...")
        try:
            import litellm

            schema_json = json.dumps(JobPosting.model_json_schema(), indent=2)
            prompt = (
                f"{self.get_llm_instructions()}\n\n"
                f"Extract the following JSON schema from the text below. "
                f"Return ONLY valid JSON, no markdown fences.\n\n"
                f"Schema:\n{schema_json}\n\n"
                f"Text:\n{markdown_content[:8000]}"
            )

            llm_cfg = self.get_llm_config()
            response = await litellm.acompletion(
                model=llm_cfg.provider,
                messages=[{"role": "user", "content": prompt}],
                api_key=llm_cfg.api_token,
                temperature=llm_cfg.temperature or 0.1,
            )

            content = response.choices[0].message.content.strip()
            # Strip markdown code fences if present
            if content.startswith("```"):
                content = content.split("\n", 1)[1] if "\n" in content else content
                if content.endswith("```"):
                    content = content[:-3].strip()

            return self._try_validate(content)
        except Exception as e:
            logger.error(f"  [❌] LLM rescue error: {e}")
            return None, f"LLM exception: {str(e)}"

    # ------------------------------------------------------------------
    # Main orchestration loop (concurrent + streaming)
    # ------------------------------------------------------------------

    async def run(
        self,
        already_scraped: List[str],
        save_html: bool = False,
        **kwargs,
    ):
        """Main scraping loop with concurrent crawling and streaming.

        Args:
            already_scraped: List of job IDs already on disk.
            save_html: If True, also save ``raw_page.html``.
            **kwargs: CLI args forwarded from main.py.
        """
        search_url = self.get_search_url(**kwargs)
        drop_repeated = kwargs.get("drop_repeated", True)

        async with AsyncWebCrawler(config=self.get_browser_config()) as crawler:
            # 1. Discover links from listing page
            logger.info(f"[*] Searching for jobs at: {search_url}")
            listing_result = await crawler.arun(
                url=search_url, config=self.get_base_crawl_config()
            )

            if not listing_result.success:
                logger.error(f"[!] Search failed: {listing_result.error_message}")
                return

            all_links = self.extract_links(listing_result)

            # 2. Filter already-scraped links BEFORE concurrent dispatch
            links_to_crawl = []
            for url in all_links:
                job_id = self.extract_job_id(url)
                if drop_repeated and job_id in already_scraped:
                    continue
                links_to_crawl.append(url)

            if not links_to_crawl:
                logger.info("[*] No new job postings.")
                return

            limit = kwargs.get("limit")
            if limit:
                links_to_crawl = links_to_crawl[:limit]

            logger.info(
                f"[*] Processing {len(links_to_crawl)} new jobs "
                f"(out of {len(all_links)} found) concurrently..."
            )

            # 3. Generate/load CSS schema ONCE using the first link
            esquema_css = await self.get_fast_schema(crawler, links_to_crawl[0])

            # 4. Prepare the run config with extraction strategy
            run_config = self.get_base_crawl_config()
            if esquema_css:
                run_config.extraction_strategy = JsonCssExtractionStrategy(
                    esquema_css
                )

            # 5. Launch concurrent multi-crawl with rate limiting
            dispatcher = self.get_dispatcher()

            results = await crawler.arun_many(
                urls=links_to_crawl,
                config=run_config,
                dispatcher=dispatcher,
            )

            for result in results:
                job_id = self.extract_job_id(result.url)
                output_dir = f"data/source/{self.source_name}/{job_id}"

                if not result.success:
                    logger.error(f"  [❌] {job_id}: {result.error_message}")
                    continue

                # 6. Try CSS extraction + Pydantic validation
                valid_data = None
                extraction_method = "none"
                extraction_error = None
                css_error = None

                if result.extracted_content:
                    valid_data, css_error = self._try_validate(result.extracted_content)
                    if valid_data:
                        extraction_method = "css"
                        logger.info(f"  [⚡] {job_id} extracted and validated.")

                # 7. LLM rescue if CSS failed — pass markdown (smaller + cleaner)
                if not valid_data:
                    md_for_llm = ""
                    if result.markdown:
                        md_for_llm = (
                            getattr(result.markdown, "fit_markdown", None)
                            or getattr(result.markdown, "raw_markdown", None)
                            or str(result.markdown)
                        )
                    valid_data, llm_error = await self._llm_rescue(md_for_llm)
                    if valid_data:
                        extraction_method = "llm"
                        logger.info(f"  [✅] {job_id} rescued by LLM.")
                    else:
                        extraction_error = f"CSS Error: {css_error} | LLM Error: {llm_error}"
                        logger.error(
                            f"  [📝] {job_id} structured extraction failed. Error: {llm_error}"
                        )

                # 8. Save artifacts (ALWAYS save Markdown and JSON)
                os.makedirs(output_dir, exist_ok=True)

                # Save clean markdown
                md_content = ""
                if result.markdown:
                    md_content = (
                        getattr(result.markdown, "fit_markdown", None)
                        or getattr(result.markdown, "raw_markdown", None)
                        or str(result.markdown)
                    )
                with open(
                    os.path.join(output_dir, "content.md"), "w", encoding="utf-8"
                ) as f:
                    f.write(md_content)

                # Save extracted JSON (or empty if failed to meet contract)
                with open(
                    os.path.join(output_dir, "extracted_data.json"),
                    "w",
                    encoding="utf-8",
                ) as f:
                    # Write the payload if valid, else an empty object
                    json.dump(valid_data or {}, f, indent=2, ensure_ascii=False)

                # Save metadata log
                import datetime
                meta_log = {
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "job_id": job_id,
                    "url": result.url,
                    "success": result.success and valid_data is not None,
                    "extraction_method": extraction_method,
                    "error": extraction_error or result.error_message,
                    "crawl_stats": result.crawl_stats or {},
                    "response_status": result.status_code,
                }
                
                with open(
                    os.path.join(output_dir, "scrape_meta.json"),
                    "w",
                    encoding="utf-8",
                ) as f:
                    json.dump(meta_log, f, indent=2, ensure_ascii=False)

                # Optional: save HTML
                if save_html and result.cleaned_html:
                    with open(
                        os.path.join(output_dir, "raw_page.html"),
                        "w",
                        encoding="utf-8",
                    ) as f:
                        f.write(result.cleaned_html)
