import os
from typing import FrozenSet
from bs4 import BeautifulSoup
import requests
import time
import json
import re

import boto3
from urllib.parse import urljoin, urlparse, urldefrag
from collections import deque
from langchain_community.document_transformers import MarkdownifyTransformer
from langchain_core.documents import Document
from ..utils import extract_domain

CRAWLER_LAMBDA_NAME = os.getenv("CRAWLER_LAMBDA_NAME",None)
CRAWL4AI_API_URL = os.getenv("CRAWL4AI_API_URL")
CRAWL4AI_API_TOKEN = os.getenv("CRAWL4AI_API_TOKEN")

class WebScraper:
    def __init__(self, max_breath=3, max_depth=2):
        self.max_breath = max_breath
        self.max_depth = max_depth
        
    def _replace_long_links(self,url,md_text):
        
        URL_LENGTH_THRESHOLD = 60

        image_pattern = re.compile(r'!\[([^\]]+)\]\(([^\)]+)\)')
        link_pattern = re.compile(r'\[([^\]]+)\]\(([^\)]+)\)')

        def replace_image(match):
            alt_text, image_url = match.group(1), match.group(2)
            image_url = urljoin(url,image_url)
            if len(image_url) > URL_LENGTH_THRESHOLD:
                return alt_text
            return f"![{alt_text}]({image_url})"

        def replace_link(match):
            link_text, link_url = match.group(1), match.group(2)
            link_url = urljoin(url,link_url)
            if len(link_url) > URL_LENGTH_THRESHOLD:
                return link_text
            return f"[{link_text}]({link_url})"

        md_text = image_pattern.sub(replace_image, md_text)
        md_text = link_pattern.sub(replace_link, md_text)
        return md_text

    def recursively_scrape(self, start_url, skip_urls: FrozenSet[str] =frozenset(),fast=True):
        """
        Crawls and scrapes web pages recursively using a queue.
        
        :param start_url: The initial URL to start crawling from.
        :param max_depth: The maximum depth of recursion.
        :param max_breadth: The maximum number of links to follow per page.
        """

        edges = []
        nodes = {}
        start_url = urldefrag(start_url).url.strip()

        # Queue stores (URL, depth)
        queue = deque([(start_url, 0)])
        
        # Set to store visited URLs
        visited = set([start_url]).union(skip_urls)
       
        while queue:
            url, depth = queue.popleft()
            
            try:

                # Fetch the page content
                result = self.crawl_page(url,pre_crawl_urls=[url2 for url2,depth2 in list(queue) if depth2==depth],fast=fast)

                if url not in skip_urls:
                    nodes[url] = Document(page_content=self._replace_long_links(url,result["markdown"]),metadata={"domain": extract_domain(url), "url": url,"title": result["metadata"]["title"], "html": result["html"]})

                # Find and process links
                absolute_urls = frozenset([urldefrag(link.get("href")).url.strip() for link in result["links"]["internal"]])

                absolute_urls = [next_url for next_url in absolute_urls if next_url not in visited and ("." not in next_url.split("/")[-1] or ".html" in next_url.split("/")[-1])]
                
                if depth >= self.max_depth:
                    continue  # Skip if depth exceeded or already visited

                # Limit the number of links per page
                for next_url in absolute_urls[:self.max_breath]:
                    visited.add(next_url)
                    queue.append((next_url, depth + 1))
                    edges.append((url,next_url))

            except requests.RequestException as e:
                print(f"Error accessing {url}: {e}")

        return nodes, [edge for edge in edges if edge[1] in nodes.keys()]

    _crawl4ai_cache = {}

    def crawl_page(self,url,pre_crawl_urls=[], fast=True):
        if fast:
            md = MarkdownifyTransformer()

            response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            for script in soup(["script", "style"]):
                script.extract()
            html = soup.prettify()
            md_document = md.transform_documents([Document(page_content=html)])[0]

            links = [{"href":urljoin(url,a.get("href")),"text": a.get("text")} for a in soup.find_all("a", href=True)]
            return {"metadata":{"title": soup.title.string if soup.title else ""}, "html": html, "markdown":md_document.page_content, "links": {"internal":[link for link in links if urlparse(link.get("href")).netloc == urlparse(url).netloc]}}
        else:
            if CRAWLER_LAMBDA_NAME:
                if  url in self._crawl4ai_cache:
                    return self._crawl4ai_cache[url]
                
                client = boto3.client("lambda")

                response = client.invoke(
                    FunctionName=CRAWLER_LAMBDA_NAME,
                    InvocationType="RequestResponse",
                    Payload=json.dumps({"urls":[url]+pre_crawl_urls}),
                )
                payload = json.loads(response['Payload'].read())
                self._crawl4ai_cache |= payload
                return self._crawl4ai_cache[url]
            else:
                import asyncio
                
                if  url in self._crawl4ai_cache:
                    return self._crawl4ai_cache[url]
                
                payload = asyncio.run(self._crawl4ai([url]+pre_crawl_urls))
                self._crawl4ai_cache |= payload
                return self._crawl4ai_cache[url]  
    
    async def _crawl4ai(self, urls):
            
        def submit_and_wait(request_data: dict, timeout: int = 300) -> list[dict]:
            headers = {"Authorization": f"Bearer {CRAWL4AI_API_TOKEN}"}
            response = requests.post(f"{CRAWL4AI_API_URL}/crawl", json=request_data, headers=headers)
            task_id = response.json()["task_id"]

            start_time = time.time()
            while True:
                if time.time() - start_time > timeout:
                    raise TimeoutError(f"Task {task_id} timeout")

                result = requests.get(f"{CRAWL4AI_API_URL}/task/{task_id}",headers=headers)
                status = result.json()

                if status["status"] == "completed":
                    return status["results"]

                time.sleep(2)
                
        browser_config_payload = {
        "type": "BrowserConfig",
        "params": {"browser_type":"chromium", "headless": True, "text_mode": True, "extra_args":["--disable-gpu", "--single-process"]}
        }
        
        crawler_config_payload = {
            "type": "CrawlerRunConfig",
            "params": {"stream": False, "cache_mode": "bypass"}
        }

        crawl_payload = {
            "urls": urls,
            "browser_config": browser_config_payload,
            "crawler_config": crawler_config_payload
        }
        
        results = {}  
        for result in submit_and_wait(crawl_payload):
            results[result["url"]] = {"metadata": result["metadata"],"html": result["html"], "markdown":result["markdown"], "links":result["links"],"pdf":result.get("pdf",None)}
        return results
