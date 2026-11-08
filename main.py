from langgraph.graph import StateGraph,START,END
from langchain.chat_models import init_chat_model
from langgraph.graph.message import MessagesState
import csv
from itertools import islice
from tools import tools
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import InMemorySaver

with open("key.csv", "r") as f:
    reader = csv.reader(f)
    llm_api_key = next(islice(reader, 0, 1))[1]

model = init_chat_model(
            model='deepseek-flash',
            base_url="https://api.deepseek.com",
            api_key=llm_api_key,
            max_tokens=1000,
            model_provider="deepseek",
            reasoning_effort="high",
            extra_body={"thinking": {"type": "enabled"}},
        )

model = model.bind_tools(tools)

graph = StateGraph(MessagesState)

tool_node = ToolNode(tools=tools)

def agent(state: MessagesState):
    messages = state["messages"]
    response = model.invoke(messages)
    return {"messages": [response]}

def condition_edge(state:MessagesState):
    if state["messages"][-1].tool_calls:
        return "tool_node"
    else:
        return END

graph.add_node("agent", agent)
graph.add_node("tool_node", tool_node)

graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", condition_edge)
graph.add_edge("tool_node", "agent")

memory_saver = InMemorySaver()
sql_agent = graph.compile(checkpointer=memory_saver)

if __name__ == "__main__":
    while True:
        user_input = input('请输入您的问题：')
        res = sql_agent.invoke({'messages':[{"role": "user", "content": user_input}]},config={'configurable': {'thread_id': 'test_01'}})
        print(res['messages'][-1].content)