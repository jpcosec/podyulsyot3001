from __future__ import annotations

import argparse
import json

from src.core.scraping.contracts import CrawlListingRequest, ScrapeDetailRequest
from src.core.scraping.service import crawl_listing, scrape_detail


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.mode in {"auto", "detail"} and _is_detail_url(args.url):
        _run_detail(source=args.source, url=args.url)
        return
    if args.mode in {"auto", "listing"}:
        _run_listing(
            source=args.source,
            url=args.url,
            max_pages=args.max_pages,
            run_id=args.run_id,
        )
        return
    _run_detail(source=args.source, url=args.url)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--mode", choices=["auto", "listing", "detail"], default="auto")
    parser.add_argument("--max-pages", type=int, default=3)
    parser.add_argument("--run-id", default="probe")
    return parser


def _run_listing(source: str, url: str, max_pages: int, run_id: str) -> None:
    result = crawl_listing(
        CrawlListingRequest(
            source=source,
            listing_url=url,
            known_ids=[],
            max_pages=max_pages,
            run_id=run_id,
        )
    )
    print("MODE listing")
    print("CODE_PATH src/core/scraping/service.py:crawl_listing")
    print(f"LISTING_URL {url}")
    print(f"DISCOVERED_IDS {len(result.discovered_ids)}")
    print(f"NEW_IDS {len(result.new_ids)}")
    if result.discovered_urls:
        print("DETAIL_URL_SAMPLE")
        for item in result.discovered_urls[:10]:
            print(item)
    print("ARTIFACT_REFS")
    print(json.dumps(result.artifact_refs, indent=2))
    print("WARNINGS")
    print(json.dumps(result.warnings, indent=2))


def _run_detail(source: str, url: str) -> None:
    result = scrape_detail(
        ScrapeDetailRequest(
            source=source,
            source_url=url,
            preferred_fetch_mode="auto",
        )
    )
    raw_text = str(result.canonical_scrape.get("raw_text") or "")
    print("MODE detail")
    print("CODE_PATH src/core/scraping/service.py:scrape_detail")
    print(f"DETAIL_URL {url}")
    print(f"FETCH_MODE {result.used_fetch_mode}")
    print(f"RAW_TEXT_LEN {len(raw_text)}")
    print("ARTIFACT_REFS")
    print(json.dumps(result.artifact_refs, indent=2))
    print("WARNINGS")
    print(json.dumps(result.warnings, indent=2))


def _is_detail_url(url: str) -> bool:
    return "-inline.html" in url or "stellenangebote--" in url


if __name__ == "__main__":
    main()
