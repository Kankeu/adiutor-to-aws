from typing import FrozenSet
import datetime
import json

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langdetect import detect

from .web_scraper import WebScraper
from ..database import StoreManager, WebPage
from ..utils import extract_domain

class WebSearch:


    def __init__(self,llm_api, store_manager: StoreManager):
        self.llm_api = llm_api
        self.web_scraper = WebScraper(max_breath=3,max_depth=2)
        self.store_manager = store_manager
        self.start_url = None
        self.max_context_len = int(4096*3.5)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.max_context_len, # Avg. length of a token is ~ 3.75 and context window 2048
            chunk_overlap=20,
            length_function=len,
            is_separator_regex=False,
        )
        headers_to_split_on = [("#", "h1"), ("##", "h2"), ("###", "h3")]
        self.markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        self.locales = {"en":"en","de":"de"}

    def get_aggregation_prompt(self,query,system_prompt,context):
        # Prompt to combine summarized page contents with sources (page identifier)
        system_prompt = system_prompt or ""
        return f"""<<SYS>>You are a useful and harmful information retriever. Based on the following web page contents of a web search answer the user query below. Formulate your answer in the Markdown syntax. Do not forget to indicate the page identifiers in your answer.
Today is {datetime.datetime.now().strftime('%B %d, %Y at %H:%M')}      
      
<</SYS>>
[INST]
Web page contents: ```
Page identifier: WSD-#1
Page content: Amor fati is a Latin phrase that translates to "love of fate" or "love of one's fate."

############################################

Page identifier: WSD-#2
Page content: Amor fati describes an attitude of accepting and even embracing everything that happens in life, both the positive and negative, with a sense of gratitude and positivity.
```

User query: What means amor fati?
[/INST]
Answer: Amor fati is a Latin phrase that translates to "love of fate" (WSD-#1) It describes an attitude of accepting and even embracing everything that happens in life (WSD-#2).

[INST]
Web page contents: ```{context}```

{system_prompt}          
User query: {query}
[/INST]
Answer:
"""

    def get_summary_prompt(self,query,system_prompt,context):
        # Prompt to summarize page contents
        return f"""<<SYS>>You are a useful and harmful information retriever. Do not mention that the text does not provide information about the query.
Today is {datetime.datetime.now().strftime('%B %d, %Y at %H:%M')}    

<</SYS>>
        
[INST]
{system_prompt}          
Summarize in detail the text below based on the following query: "{query}".

Text: ```{context}```
[/INST]
Summary:
"""
    
    def index(self, start_url: str):
        
        indexed_urls = frozenset(wp.url for wp in self.store_manager.db.query(WebPage).filter(WebPage.domain == extract_domain(start_url)).all())
        
        nodes,_ = self.web_scraper.recursively_scrape(start_url=start_url, skip_urls=indexed_urls)
            
        md_splits = [Document(page_content=md_split.page_content,metadata={"url":node.metadata["url"],"title":node.metadata["title"]}) for node in nodes.values() for md_split in self.markdown_splitter.split_text(node.page_content)]

        splits = self.text_splitter.split_documents(md_splits)
        try:
            lang = self.locales.get(detect(splits[0].page_content))
        except:
            lang = "en"

        # Indexing with FAISS
        self.store_manager.denspa.add_documents(splits, lang=lang, engine="faiss")

        # Indexing with BM25
        self.store_manager.denspa.add_documents(splits, lang=lang, engine="bm25")

        # Add the web pages in the database
        for node in nodes.values():
            self.store_manager.db.add(WebPage(domain=node.metadata["domain"], url=node.metadata["url"], title=node.metadata["title"], html=node.metadata["html"]))
        
        # Save the index and db locally/s3
        self.store_manager.save()
        
        return {"status":"done", "payload": self.store_manager.db.query(WebPage).all()}

    def delete(self, urls: FrozenSet[str]):

        for url in urls:
            self.store_manager.denspa.removeByMetadata({"url": url})
        
        self.store_manager.db.query(WebPage).filter(WebPage.url.in_(urls)).delete(synchronize_session=False)
        self.store_manager.save()

        return {"status":"done", "payload": self.store_manager.db.query(WebPage).all()}
    
    async def process(self,query,system_prompt):

        try:
            lang = self.locales.get(detect(query))
        except:
            lang = "en"

        results = self.store_manager.denspa.similarity_search_with_score(
            query=query,
            k=10,
            method="faiss",
            lang=lang
        )

        sources = [dict(id=f"WSD-#{i+1}",url=r[0].metadata["url"],title=r[0].metadata["title"],text=r[0].page_content,score=float(r[1])) for i,r in enumerate(results)]
        yield json.dumps({"status":"ok","type":"metadata","payload":{"cost": round(len((" ".join(r[0].page_content for r in results)).split()) / 10), "sources": sources}})
        context = ""
        for i,res in enumerate(results):
            # Model context is limited
            if len(context) > self.max_context_len:
                continue
            summary = self.llm_api.generate(self.get_summary_prompt(query,system_prompt,res[0].page_content))
            context += f"""
Page identifier: WSD-#{i+1}
Page content: {summary}

############################################

"""
        response = self.llm_api.generate(self.get_aggregation_prompt(query,system_prompt,context))
        yield json.dumps({"status":"ok","type":"web_search","payload":{"response":response}})

        yield json.dumps({"status":"done","type":"web_search","payload":None})