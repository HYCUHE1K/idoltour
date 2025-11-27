"""Scrapy settings for the movie agent project."""

BOT_NAME = "movie_agent"

SPIDER_MODULES = ["movie_agent.spiders"]
NEWSPIDER_MODULE = "movie_agent.spiders"

ROBOTSTXT_OBEY = True
DOWNLOAD_TIMEOUT = 15
CONCURRENT_REQUESTS = 8

ITEM_PIPELINES = {
    "movie_agent.pipelines.TopKPipeline": 300,
}

DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/118.0 Safari/537.36"
    ),
}

TOP_K = 3
