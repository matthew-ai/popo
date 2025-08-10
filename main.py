from dotenv import load_dotenv
from pathlib import Path
import os
load_dotenv(dotenv_path=Path(os.path.join(os.path.dirname(__file__), ".env")), verbose=True)


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
    # question = "当前项目是如何实现读文件的"
    question = "帮我查找项目中有关提示词模板的内容"
    query(question)
