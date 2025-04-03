import asyncio

from crawl4ai import *


def handler(event, context):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(crawl(event["urls"]))

async def crawl(urls):
    crawler = AsyncWebCrawler(config=BrowserConfig(
        browser_type="chromium",
        headless=True,
        text_mode=True,
        extra_args=["--disable-gpu", "--single-process"])
    )
    results = {}
    await crawler.start()
    for url in urls:
        result = await crawler.arun(url)
        results[url] = {"metadata": result.metadata, "markdown":result.markdown.raw_markdown, "links":result.links,"pdf":result.pdf}
    await crawler.close()
    return results
