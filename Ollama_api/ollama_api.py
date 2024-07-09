import requests
import json

# 提供api获取ollama 模型列表
def get_llm():
    respone = requests.get(url="http://localhost:11434/api/tags")
    result = json.loads(respone.content)
    llms = []
    for llm in result["models"]:
        if "code" not in llm["name"] and "embed" not in llm["name"]:
            llms.append(llm["name"])
    return llms

def get_embeding_model():
    respone = requests.get(url="http://localhost:11434/api/tags")
    result = json.loads(respone.content)
    llms = []
    for llm in result["models"]:
        if "embed" in llm["name"]:
            llms.append(llm["name"])
    return llms
