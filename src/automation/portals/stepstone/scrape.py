"""StepStone scrape portal definition in Ariadne common language."""
from src.automation.ariadne.models import ScrapePortalDefinition

STEPSTONE_SCRAPE = ScrapePortalDefinition(
    source_name="stepstone",
    base_url="https://www.stepstone.de",
    supported_params=["job_query", "city", "max_days"],
    job_id_pattern=r"--(\d+)-inline\.html",
)
