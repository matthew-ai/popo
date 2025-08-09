from dotenv import load_dotenv
from pathlib import Path
load_dotenv(dotenv_path=Path(".env"), verbose=True)


from agent.react_agent import create_agent

def query(question: str):
    react_agent = create_agent()
    result = react_agent.invoke(
        {
            "messages": [
                {"role": "user", "content": question}
            ]
        }
    )
    print(result)




if __name__ == "__main__":
    question = "what is the weather in sf?"
    query(question)
