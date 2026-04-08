import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from mcp_tools import mcp

llm = ChatOpenAI(model="gpt-4-turbo", temperature=0)

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], list.__add__]
    next_agent: str

def supervisor_node(state: AgentState):
    last_msg = state["messages"][-1].content.lower()
    if "task" in last_msg or "add" in last_msg:
        return {"next_agent": "task_agent"}
    return {"next_agent": "FINISH", "messages": [AIMessage(content="Cloud workflow complete.")]}

def task_agent_node(state: AgentState):
    # Packaged tool arguments as a dictionary to prevent MCP 500 errors
    tool_args = {"user_id": 1, "description": "Cloud Deployed Task", "due_date": "ASAP"}
    response = mcp.call_tool("add_task", tool_args)
    return {"messages": [AIMessage(content=str(response))], "next_agent": "supervisor"}

workflow = StateGraph(AgentState)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("task_agent", task_agent_node)
workflow.set_entry_point("supervisor")
workflow.add_conditional_edges("supervisor", lambda x: x["next_agent"], {"task_agent": "task_agent", "FINISH": END})
workflow.add_edge("task_agent", "supervisor")
app_graph = workflow.compile()

app = FastAPI(title="Cloud Multi-Agent API")

class RequestModel(BaseModel):
    query: str

@app.post("/api/v1/assist")
async def assist(request: RequestModel):
    try:
        result = app_graph.invoke({"messages": [HumanMessage(content=request.query)]})
        ai_messages = [m.content for m in result["messages"] if isinstance(m, AIMessage)]
        return {"status": "success", "response": ai_messages[-1]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
import os

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))