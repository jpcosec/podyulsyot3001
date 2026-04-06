"""TU Berlin scrape portal definition in Ariadne common language."""
from src.automation.ariadne.models import ScrapePortalDefinition

TUBERLIN_SCRAPE = ScrapePortalDefinition(
    source_name="tuberlin",
    base_url="https://www.jobs.tu-berlin.de",
    supported_params=["categories", "job_query"],
    job_id_pattern=r"/job-postings/(\d+)",
)
