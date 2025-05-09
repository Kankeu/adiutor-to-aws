import asyncio
from langchain_openai import ChatOpenAI

# Interface to communicate with OpenAI's LLM model
class LLMAPI:

    def __init__(self):
        self.llm = ChatOpenAI(max_tokens=4096,temperature=0,model="gpt-4.1-nano-2025-04-14")

    def generate(
            self,
            prompt,
    ):
        return self.llm.invoke([("human",prompt)]).content

    def iter_over_async(self,ait, loop=asyncio.new_event_loop()):
        ait = ait.__aiter__()
        async def get_next():
            try: obj = await ait.__anext__(); return False, obj
            except StopAsyncIteration: return True, None
        while True:
            done, obj = loop.run_until_complete(get_next())
            if done: break
            yield obj