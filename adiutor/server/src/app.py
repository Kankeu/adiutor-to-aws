import os
from typing import List

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from mangum import Mangum
from pydantic import BaseModel, HttpUrl
from .database import StoreManager, WebPage
from .llm.llm_api import LLMAPI
from .web_search import WebSearch

app = FastAPI()

# Initialize the sqlite and vector database
store_manager = StoreManager()
store_manager.load()

BACKEND_ENV = os.environ.get("BACKEND_ENV",None)
IS_PROD = BACKEND_ENV=="prod"

if not IS_PROD:
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

handler = Mangum(app)

# API Token of LLM
llm_api = LLMAPI()

web_search = WebSearch(llm_api=llm_api,store_manager=store_manager)

class QueryReq(BaseModel):
    query: str 
    system_prompt: str = ""

@app.post("/api/query")
def query(data: QueryReq):
    return StreamingResponse(llm_api.iter_over_async(web_search.process(data.query,data.system_prompt)))

class IndexReq(BaseModel):
    url: HttpUrl
    fast: bool = True

@app.post("/api/index")
def index(data: IndexReq):
    return web_search.index(str(data.url),fast=data.fast)

@app.get("/api/web_pages")
def web_pages():
    return {"status": "done", "payload": store_manager.db.query(WebPage).all()}

class DeleteWebPage(BaseModel):
    urls: List[str] = []
    domains: List[str] = []
    
@app.post("/api/web_pages/delete")
def web_pages(data: DeleteWebPage):
    urls = frozenset(data.urls).union(frozenset(wp.url for wp in store_manager.db.query(WebPage).filter(WebPage.domain.in_(data.domains)).all()))
    return web_search.delete(urls)

@app.get("/api/config")
def config():
    return {"version": "0.0.2"}