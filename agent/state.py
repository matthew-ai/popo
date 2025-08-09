from pydantic import BaseModel
from typing import Annotated
from langgraph.graph import add_messages
from langchain.schema import BaseMessage


class State(BaseModel):
    messages: Annotated[list[BaseMessage], add_messages]
    remaining_steps: int = 50
