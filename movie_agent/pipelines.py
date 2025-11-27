"""Item pipelines for ranking and collecting movie results."""

from __future__ import annotations

from typing import List

from scrapy import Spider

from movie_agent.items import MovieItem


class TopKPipeline:
    """Accumulates items and keeps only the top-k based on score."""

    def __init__(self, k: int = 3):
        self.k = k
        self._items: List[MovieItem] = []

    @classmethod
    def from_crawler(cls, crawler):
        k = crawler.settings.getint("TOP_K", 3)
        return cls(k=k)

    def process_item(self, item: MovieItem, spider: Spider):
        self._items.append(item)
        return item

    def close_spider(self, spider: Spider):
        sorted_items = sorted(
            self._items,
            key=lambda item: item.get("score", 0),
            reverse=True,
        )
        top_items = sorted_items[: self.k]

        if hasattr(spider, "collector") and getattr(spider, "collector") is not None:
            spider.collector.results = [dict(item) for item in top_items]

        spider.logger.info("Top %s results:", self.k)
        for idx, item in enumerate(top_items, start=1):
            spider.logger.info(
                "%s. %s (%s) %s score=%s",
                idx,
                item.get("title"),
                item.get("year", "n/a"),
                item.get("source"),
                item.get("score"),
            )
