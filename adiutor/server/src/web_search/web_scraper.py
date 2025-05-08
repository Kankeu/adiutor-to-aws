import os
from typing import FrozenSet
from bs4 import BeautifulSoup
import requests
import json

import boto3
from urllib.parse import urljoin, urlparse, urldefrag
from collections import deque
from langchain_community.document_transformers import MarkdownifyTransformer
from langchain_core.documents import Document
from ..utils import extract_domain

CRAWLER_LAMBDA_NAME = os.getenv("CRAWLER_LAMBDA_NAME",None)

class WebScraper:
    def __init__(self, max_breath=3, max_depth=2):
        self.max_breath = max_breath
        self.max_depth = max_depth

    def recursively_scrape(self, start_url, skip_urls: FrozenSet[str] =frozenset()):
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
                result = self.crawl_page(url,pre_crawl_urls=[url2 for url2,depth2 in list(queue) if depth2==depth])

                if url not in skip_urls:
                    nodes[url] = Document(page_content=result["markdown"],metadata={"domain": extract_domain(url), "url": url,"title": result["metadata"]["title"], "html": result["html"]})

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

    _crawer_lambda = {}

    def crawl_page(self,url,pre_crawl_urls=[]):
        if CRAWLER_LAMBDA_NAME:
            if  url in self._crawer_lambda:
                return self._crawer_lambda[url]
            
            client = boto3.client("lambda")

            response = client.invoke(
                FunctionName=CRAWLER_LAMBDA_NAME,
                InvocationType="RequestResponse",
                Payload=json.dumps({"urls":[url]+pre_crawl_urls}),
            )
            payload = json.loads(response['Payload'].read())
            self._crawer_lambda |= payload
            return self._crawer_lambda[url]
        else:
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
    