import os
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
import memory
import tools as T

SYSTEM = ("You are an autonomous research assistant. Use tools when needed: "
          "calculator for maths, wikipedia_search/arxiv_search for facts and papers, "
          "weather for current weather, fetch_url for allowlisted pages. "
          "Cite which tool you used. Be concise.")

TOOLS = [tool(f) for f in (T.calculator, T.wikipedia_search, T.arxiv_search, T.weather, T.fetch_url)]


def build_agent():
    llm = ChatGroq(model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"), temperature=0)
    return create_react_agent(llm, TOOLS, prompt=SYSTEM)


def chat(agent, thread_id: str, user_message: str) -> str:
    msgs = memory.history(thread_id, limit=10) + [("user", user_message)]
    out = agent.invoke({"messages": msgs})
    reply = out["messages"][-1].content
    memory.add(thread_id, "user", user_message)
    memory.add(thread_id, "assistant", reply)
    return reply
