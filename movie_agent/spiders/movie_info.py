"""Spider that retrieves movie information from several public sources."""

from __future__ import annotations

import json
import re
import urllib.parse
from typing import Iterable, List, Optional, Sequence

import scrapy
from rapidfuzz import fuzz

from movie_agent.items import MovieItem


class MovieInfoSpider(scrapy.Spider):
    name = "movie_info"
    allowed_domains = [
        "v2.sg.media-imdb.com",
        "api.tvmaze.com",
        "en.wikipedia.org",
    ]

    default_sources: Sequence[str] = ("imdb", "tvmaze", "wikipedia")

    def __init__(
        self,
        query: str,
        sources: Optional[List[str]] = None,
        max_results: int = 5,
        collector=None,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        normalized = self._normalize_query(query)
        if not normalized:
            raise ValueError("A non-empty movie title is required.")

        self.query = normalized
        self.sources = tuple(sources) if sources else self.default_sources
        self.max_results = max(1, int(max_results))
        self.collector = collector

    async def start(self):
        for request in self.start_requests():
            yield request

    def start_requests(self) -> Iterable[scrapy.Request]:
        for source in self.sources:
            builder = getattr(self, f"_request_{source}", None)
            if not builder:
                self.logger.warning("Unknown source '%s' skipped.", source)
                continue
            yield builder()

    # Request builders -------------------------------------------------

    def _request_imdb(self) -> scrapy.Request:
        encoded = urllib.parse.quote(self.query.lower())
        first_letter = self.query[0].lower()
        if not first_letter.isascii():
            first_letter = "1"
        prefix = urllib.parse.quote(first_letter)
        url = f"https://v2.sg.media-imdb.com/suggestion/{prefix}/{encoded}.json"
        return scrapy.Request(
            url,
            callback=self.parse_imdb,
            cb_kwargs={"source": "imdb"},
        )

    def _request_tvmaze(self) -> scrapy.Request:
        encoded = urllib.parse.quote(self.query)
        url = f"https://api.tvmaze.com/search/shows?q={encoded}"
        return scrapy.Request(
            url,
            callback=self.parse_tvmaze,
            cb_kwargs={"source": "tvmaze"},
        )

    def _request_wikipedia(self) -> scrapy.Request:
        encoded = urllib.parse.quote(self.query)
        url = (
            "https://en.wikipedia.org/w/api.php?action=opensearch&"
            f"search={encoded}&limit={self.max_results}&namespace=0&format=json"
        )
        return scrapy.Request(
            url,
            callback=self.parse_wikipedia,
            cb_kwargs={"source": "wikipedia"},
        )

    # Parsers ----------------------------------------------------------

    def parse_imdb(self, response: scrapy.http.Response, source: str):
        data = json.loads(response.text)
        for entry in data.get("d", [])[: self.max_results]:
            title = entry.get("l")
            year = entry.get("y")
            summary = entry.get("s")
            imdb_id = entry.get("id")
            url = f"https://www.imdb.com/title/{imdb_id}" if imdb_id else None

            item = self._build_item(
                title=title,
                year=str(year) if year else None,
                director=None,
                rating=entry.get("rank"),
                summary=summary,
                source=source,
                url=url,
            )
            yield item

    def parse_tvmaze(self, response: scrapy.http.Response, source: str):
        data = json.loads(response.text)
        for entry in data[: self.max_results]:
            show = entry.get("show") or {}
            title = show.get("name")
            premiered = show.get("premiered")
            year = premiered.split("-")[0] if premiered else None
            summary = self._strip_html(show.get("summary"))

            item = self._build_item(
                title=title,
                year=year,
                director=None,
                rating=show.get("rating", {}).get("average"),
                summary=summary,
                source=source,
                url=show.get("url"),
            )
            yield item

    def parse_wikipedia(self, response: scrapy.http.Response, source: str):
        data = json.loads(response.text)
        if len(data) < 4:
            return

        titles, descriptions, urls = data[1], data[2], data[3]
        for title, description, url in zip(
            titles[: self.max_results],
            descriptions[: self.max_results],
            urls[: self.max_results],
        ):
            item = self._build_item(
                title=title,
                year=self._extract_year(description),
                director=None,
                rating=None,
                summary=description,
                source=source,
                url=url,
            )
            yield item

    # Helpers ----------------------------------------------------------

    def _build_item(self, **kwargs) -> MovieItem:
        item = MovieItem()
        for key, value in kwargs.items():
            item[key] = value
        item["score"] = float(self._compute_score(item.get("title"), item.get("year")))
        return item

    def _compute_score(self, title: Optional[str], year: Optional[str]) -> float:
        if not title:
            return 0.0
        title_score = fuzz.token_set_ratio(self.query, title)
        year_bonus = 0
        if year and year in self.query:
            year_bonus = 10
        return title_score + year_bonus

    @staticmethod
    def _strip_html(text: Optional[str]) -> Optional[str]:
        if not text:
            return None
        return re.sub(r"<[^>]+>", "", text).strip()

    @staticmethod
    def _extract_year(text: Optional[str]) -> Optional[str]:
        if not text:
            return None
        match = re.search(r"(19|20)\d{2}", text or "")
        return match.group(0) if match else None

    @staticmethod
    def _normalize_query(query: str) -> str:
        if not query:
            return ""
        return " ".join(query.split())
