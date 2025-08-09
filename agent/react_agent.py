from langgraph.prebuilt import create_react_agent
from llm_model.qwen import llm_model
from agent.tools.example import get_weather

def create_agent():
    chat_model = llm_model
    tools = [
        get_weather
    ]
    agent = create_react_agent(
        model=chat_model,
        tools=tools,
        prompt="never answer questions about the weather",
        name="popo",
    )
    return agent


