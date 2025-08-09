from dotenv import load_dotenv
from pathlib import Path
load_dotenv(dotenv_path=Path(".env"), verbose=True)


from agent.react_agent import create_agent

def query(question: str):
    react_agent = create_agent()
    result = react_agent.stream(
        {
            "messages": [
                {"role": "user", "content": question}
            ]
        }
    )
    for chunk in result:
        print(chunk)




if __name__ == "__main__":
    question = "最近提交代码的是谁，提交信息是什么？"
    query(question)
