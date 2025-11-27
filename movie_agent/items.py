"""Item definitions for the movie agent."""

from typing import Optional

import scrapy


class MovieItem(scrapy.Item):
    title: Optional[str] = scrapy.Field()
    year: Optional[str] = scrapy.Field()
    director: Optional[str] = scrapy.Field()
    rating: Optional[float] = scrapy.Field()
    summary: Optional[str] = scrapy.Field()
    source: Optional[str] = scrapy.Field()
    url: Optional[str] = scrapy.Field()
    score: Optional[float] = scrapy.Field()
