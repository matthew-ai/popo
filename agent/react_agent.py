from langgraph.prebuilt import create_react_agent
from llm_model.qwen import llm_model
from agent.state import State
from prompt.load_template import load_prompt_template
from utils.project_structure import get_project_structure_xml

def create_agent():
    chat_model = llm_model
    prompt = load_prompt_template("code_sys", context=get_project_structure_xml())
    tools = []
    agent = create_react_agent(
        model=chat_model,
        tools=tools,
        prompt=prompt,
        state_schema=State,
        name="popo",
    )
    return agent


