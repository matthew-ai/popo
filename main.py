from dotenv import load_dotenv
from pathlib import Path
load_dotenv(dotenv_path=Path(".env"), verbose=True)



from llm_model.qwen import llm_model

print(llm_model.invoke("你是谁"))