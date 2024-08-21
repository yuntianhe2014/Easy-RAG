from langchain_community.llms import Ollama
from Config.config import neo4j_model

# 测试了 llama3：8b,gemma2:9b,qwen2:7b,glm4:9b，arcee-ai/arcee-agent:latest  目前来看 qwen2:7 效果最好
llm = Ollama(model=neo4j_model)

json_example = {'edges': [
    {
        'label': 'label 1',
        'source': 'source 1',
        'target': 'target 1'},
    {
        'label': 'label 1',
        'source': 'source 1',
        'target': 'target 1'}
],
    'nodes': [{'name': 'label 1'},
              {'name': 'label 2'},
              {'name': 'label 3'}]
}

__retriever_prompt = f"""
            您是一名专门从事知识图谱创建的人工智能专家，目标是根据给定的输入或请求捕获关系。
            基于各种形式的用户输入，如段落、电子邮件、文本文件等。
            你的任务是根据输入创建一个知识图谱。
            nodes中每个元素只有一个name参数，name对应的值是一个实体，实体来自输入的词语或短语。
             edges还必须有一个label参数，其中label是输入中的直接词语或短语,edges中的source和target取自nodes中的name。

            仅使用JSON进行响应，其格式可以在python中进行jsonify，并直接输入cy.add（data），
            您可以参考给定的示例：{json_example}。存储node和edge的数组中，最后一个元素后边不要有逗号，
            确保边的目标和源与现有节点匹配。
            不要在JSON的上方和下方包含markdown三引号，直接用花括号括起来。
            """


def generate_graph_info(raw_text: str) -> str | None:
    """
    generate graph info from raw text
    :param raw_text:
    :return:
    """
    messages = [
        {"role": "system", "content": "你现在扮演信息抽取的角色，要求根据用户输入和AI的回答，正确提取出信息,记得不多对实体进行翻译。"},
        {"role": "user", "content": raw_text},
        {"role": "user", "content": __retriever_prompt}
    ]
    print("解析中....")
    for i in range(3):
        graph_info_result = llm.invoke(messages)
        if len(graph_info_result) < 10:
            print("-------", i, "-------------------")
            continue
        else:
            break
    print(graph_info_result)
    return graph_info_result


def update_graph(raw_text):
    #     raw_text = request.json.get('text', '')
    try:
        result = generate_graph_info(raw_text)
        if '```' in result:
            graph_data = eval(result.split('```', 2)[1].replace("json", ''))
        else:
            graph_data = eval(str(result))
        return graph_data
    except Exception as e:
        return {'error': f"Error parsing graph data: {str(e)}"}