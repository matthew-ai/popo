from dotenv import load_dotenv
from pathlib import Path
load_dotenv(dotenv_path=Path(".env"), verbose=True)


from agent.react_agent import create_agent

def query(question: str):
    pass



if __name__ == "__main__":
    # question = "What is the capital of France?"
    # query(question)

    react_agent = create_agent()
    print(react_agent.invoke(
        {
            "messages": [
                {"role": "user", "content": "what is the weather in sf"}
            ]
        }
    ))