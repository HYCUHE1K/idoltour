"""Command line interface for the Scrapy-based movie agent."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import List, Optional

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from movie_agent.spiders.movie_info import MovieInfoSpider


class ResultCollector:
    """Simple container to capture results from the pipeline."""

    def __init__(self) -> None:
        self.results: List[dict] = []


def run_agent(
    title: str,
    *,
    top_k: int = 3,
    per_source_limit: int = 5,
    sources: Optional[List[str]] = None,
    verbose: bool = False,
) -> List[dict]:
    os.environ.setdefault("SCRAPY_SETTINGS_MODULE", "movie_agent.settings")
    settings = get_project_settings()
    settings.set("TOP_K", top_k)
    settings.set("LOG_LEVEL", "INFO" if verbose else "WARNING", priority="cmdline")

    collector = ResultCollector()
    process = CrawlerProcess(settings)
    process.crawl(
        MovieInfoSpider,
        query=title,
        sources=sources,
        max_results=per_source_limit,
        collector=collector,
    )
    process.start()
    return collector.results


def format_output(results: List[dict], output: str) -> str:
    if output == "json":
        return json.dumps(results, ensure_ascii=False, indent=2)

    lines = []
    for idx, item in enumerate(results, start=1):
        line = (
            f"{idx}. {item.get('title')} ({item.get('year', 'n/a')}) "
            f"[{item.get('source')}] score={item.get('score', 0):.1f}"
        )
        lines.append(line)
        url = item.get("url")
        if url:
            lines.append(f"   URL: {url}")
        summary = item.get("summary")
        if summary:
            lines.append(f"   Summary: {summary}")
    return "\n".join(lines)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrapy agent that retrieves movie details and ranks them.",
    )
    parser.add_argument("title", help="Movie title to search for.")
    parser.add_argument(
        "--top",
        type=int,
        default=3,
        help="How many ranked results to display (default: 3).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="How many entries to keep per source (default: 5).",
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=["imdb", "tvmaze", "wikipedia"],
        help="Optional subset of sources to query.",
    )
    parser.add_argument(
        "--output",
        choices=["table", "json"],
        default="table",
        help="Output format.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose Scrapy logging.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    results = run_agent(
        args.title,
        top_k=args.top,
        per_source_limit=args.limit,
        sources=args.sources,
        verbose=args.verbose,
    )

    if not results:
        print("No matching movies found.", file=sys.stderr)
        return 1

    print(format_output(results, args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
