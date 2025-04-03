import datetime
import os


import json
import shutil

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langdetect import detect
from denspa import VectorSearch
from .web_scraper import WebScraper

BUCKET_NAME = os.environ.get("BUCKET_NAME",None)
BACKEND_ENV = os.environ.get("BACKEND_ENV",None)
IS_PROD = BACKEND_ENV=="prod"
if IS_PROD:
    import boto3
    from langchain_aws import BedrockEmbeddings

    s3 = boto3.client("s3")
    bedrock = boto3.client(service_name="bedrock-runtime")
    INDEX_PATH = "/tmp/database/index"
    EMBEDDING_FUNCTION = BedrockEmbeddings(model_id="amazon.titan-embed-text-v2:0",client=bedrock)
else:
    s3 = None
    EMBEDDING_FUNCTION = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    INDEX_PATH = "database/index"
INDEX_NAME = "denspa"

class WebSearch:


    def __init__(self,llm_api):
        self.llm_api = llm_api
        self.web_scraper = WebScraper(max_breath=3,max_depth=2)
        self.denspa = None
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
    
    def index(self,start_url):
        self.load_denspa()

        nodes,edges = self.web_scraper.recursively_scrape(start_url=start_url)
        md_splits = [Document(page_content=md_split.page_content,metadata=node.metadata | {"headers":md_split.metadata}) for node in nodes.values() for md_split in self.markdown_splitter.split_text(node.page_content)]

        splits = self.text_splitter.split_documents(md_splits)
        try:
            lang = self.locales.get(detect(splits[0].page_content))
        except:
            lang = "en"

        # Indexing with FAISS
        self.denspa.add_documents(splits, lang=lang, engine="faiss")

        # Indexing with BM25
        self.denspa.add_documents(splits, lang=lang, engine="bm25")

        # Save the index locally
        self.save_denspa()

        return {"nodes":nodes,"edges":edges}

    async def process(self,query,system_prompt):
        self.load_denspa()

        try:
            lang = self.locales.get(detect(query))
        except:
            lang = "en"

        results = self.denspa.similarity_search_with_score(
            query=query,
            k=10,
            method="cascade",
            lang=lang
        )

        sources = [dict(id=i,url=r[0].metadata["url"],title=r[0].metadata["title"],text=r[0].page_content,score=float(r[1])) for i,r in enumerate(results)]
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


    def load_denspa(self):
        if self.denspa is not None:
            return self.denspa

        if os.path.exists(INDEX_PATH):
            shutil.rmtree(INDEX_PATH)
        os.makedirs(INDEX_PATH)

        if IS_PROD:
            self.load_denspa_from_s3(INDEX_PATH, INDEX_NAME)

        self.denspa = VectorSearch(
            folder_path=INDEX_PATH,
            index_name=INDEX_NAME,
            embedding_function=EMBEDDING_FUNCTION,
            bm25_options={"k1": 1.25, "b": 0}
        )

    def save_denspa(self):
        self.denspa.save_local()

        if IS_PROD:
            self.save_denspa_to_s3(INDEX_PATH, INDEX_NAME)

    def save_denspa_to_s3(self, folder_path, key):
        try:
            for ext in [".faiss",".pkl",".bm25.index.pkl",".bm25.doc_store.pkl"]:
                s3.upload_file(Bucket=BUCKET_NAME, Key=key+ext, Filename=f"{folder_path}/{key}{ext}")
        except Exception as e:
            print(f"save_denspa_to_s3",e)


    def load_denspa_from_s3(self, folder_path, key):
        try:
            for ext in [".faiss",".pkl",".bm25.index.pkl",".bm25.doc_store.pkl"]:
                s3.download_file(Bucket=BUCKET_NAME, Key=key+ext, Filename=f"{folder_path}/{key}{ext}")
        except Exception as e:
            print("load_denspa_from_s3",e)