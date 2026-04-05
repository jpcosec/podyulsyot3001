"""XING scrape portal definition in Ariadne common language."""
from src.automation.ariadne.portal_models import ScrapePortalDefinition

XING_SCRAPE = ScrapePortalDefinition(
    source_name="xing",
    base_url="https://www.xing.com",
    supported_params=["job_query", "city", "max_days"],
    job_id_pattern=r"-(\d+)$",
)
