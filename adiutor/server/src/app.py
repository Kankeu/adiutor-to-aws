import os


from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from mangum import Mangum
from pydantic import BaseModel, HttpUrl

from .llm.llm_api import LLMAPI
from .web_search import WebSearch

app = FastAPI()

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

web_search = WebSearch(llm_api=llm_api)

DISABLE_NEST_ASYNCIO=True

class QueryReq(BaseModel):
    query: str 
    system_prompt: str = ""

@app.post("/api/query")
def query(data: QueryReq):
    return StreamingResponse(llm_api.iter_over_async(web_search.process(data.query,data.system_prompt)))

class LinkReq(BaseModel):
    url: HttpUrl

@app.post("/api/index")
def index(data: LinkReq):
    return {"url": str(data.url), "graph": web_search.index(str(data.url))}

@app.get("/api/config")
def config():
    return {"version": "0.0.1"}