import gradio as gr
import threading
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import requests
import json

# 假设这些是您的自定义模块，需要根据实际情况进行调整
from Config.config import VECTOR_DB, DB_directory
from Ollama_api.ollama_api import *
from rag.rag_class import *

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 根据VECTOR_DB选择合适的向量数据库
if VECTOR_DB == 1:
    from embeding.chromadb import ChromaDB as vectorDB
    vectordb = vectorDB(persist_directory=DB_directory)
elif VECTOR_DB == 2:
    from embeding.faissdb import FaissDB as vectorDB
    vectordb = vectorDB(persist_directory=DB_directory)
elif VECTOR_DB == 3:
    from embeding.elasticsearchStore import ElsStore as vectorDB
    vectordb = vectorDB()

# 存储上传的文件
uploaded_files = []

@lru_cache(maxsize=100)
def get_knowledge_base_files():
    cl_dict = {}
    cols = vectordb.get_all_collections_name()
    for c_name in cols:
        cl_dict[c_name] = vectordb.get_collcetion_content_files(c_name)
    return cl_dict

knowledge_base_files = get_knowledge_base_files()

def upload_files(files):
    if files:
        new_files = [file.name for file in files]
        uploaded_files.extend(new_files)
        update_knowledge_base_files()
        logger.info(f"Uploaded files: {new_files}")
        return update_file_list(), new_files, "<div style='color: green; padding: 10px; border: 2px solid green; border-radius: 5px;'>Upload successful!</div>"
    update_knowledge_base_files()
    return update_file_list(), [], "<div style='color: red; padding: 10px; border: 2px solid red; border-radius: 5px;'>Upload failed!</div>"

def delete_files(selected_files):
    global uploaded_files
    uploaded_files = [f for f in uploaded_files if f not in selected_files]
    if selected_files:
        update_knowledge_base_files()
        logger.info(f"Deleted files: {selected_files}")
        return update_file_list(), "<div style='color: green; padding: 10px; border: 2px solid green; border-radius: 5px;'>Delete successful!</div>"
    update_knowledge_base_files()
    return update_file_list(), "<div style='color: red; padding: 10px; border: 2px solid red; border-radius: 5px;'>Delete failed!</div>"

def delete_collection(selected_knowledge_base):
    if selected_knowledge_base and selected_knowledge_base != "创建知识库":
        vectordb.delete_collection(selected_knowledge_base)
        update_knowledge_base_files()
        logger.info(f"Deleted collection: {selected_knowledge_base}")
        return update_knowledge_base_dropdown(), "<div style='color: green; padding: 10px; border: 2px solid green; border-radius: 5px;'>Collection deleted successfully!</div>"
    return update_knowledge_base_dropdown(), "<div style='color: red; padding: 10px; border: 2px solid red; border-radius: 5px;'>Delete collection failed!</div>"

async def async_vectorize_files(selected_files, selected_knowledge_base, new_kb_name, chunk_size, chunk_overlap):
    if selected_files:
        if selected_knowledge_base == "创建知识库":
            knowledge_base = new_kb_name
            vectordb.create_collection(selected_files, knowledge_base, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        else:
            knowledge_base = selected_knowledge_base
            vectordb.add_chroma(selected_files, knowledge_base, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        if knowledge_base not in knowledge_base_files:
            knowledge_base_files[knowledge_base] = []
        knowledge_base_files[knowledge_base].extend(selected_files)

        logger.info(f"Vectorized files: {selected_files} for knowledge base: {knowledge_base}")
        await asyncio.sleep(0)  # 允许其他任务执行
        return f"Vectorized files: {', '.join(selected_files)}\nKnowledge Base: {knowledge_base}\nUploaded Files: {', '.join(uploaded_files)}", "<div style='color: green; padding: 10px; border: 2px solid green; border-radius: 5px;'>Vectorization successful!</div>"
    return "", "<div style='color: red; padding: 10px; border: 2px solid red; border-radius: 5px;'>Vectorization failed!</div>"

def update_file_list():
    return gr.update(choices=uploaded_files, value=[])

def search_knowledge_base(selected_knowledge_base):
    if selected_knowledge_base in knowledge_base_files:
        kb_files = knowledge_base_files[selected_knowledge_base]
        return gr.update(choices=kb_files, value=[])
    return gr.update(choices=[], value=[])

def update_knowledge_base_files():
    global knowledge_base_files
    knowledge_base_files = get_knowledge_base_files()

# 处理聊天消息的函数
chat_history = []

def safe_chat_response(model_dropdown, vector_dropdown, chat_knowledge_base_dropdown, chain_dropdown, message):
    try:
        return chat_response(model_dropdown, vector_dropdown, chat_knowledge_base_dropdown, chain_dropdown, message)
    except Exception as e:
        logger.error(f"Error in chat response: {str(e)}")
        return f"<div style='color: red;'>Error: {str(e)}</div>", ""

def chat_response(model_dropdown, vector_dropdown, chat_knowledge_base_dropdown, chain_dropdown, message):
    global chat_history
    if message:
        chat_history.append(("User", message))
        if chat_knowledge_base_dropdown == "仅使用模型":
            rag = RAG_class(model=model_dropdown,persist_directory=DB_directory)
            answer = rag.mult_chat(chat_history)
        if chat_knowledge_base_dropdown and chat_knowledge_base_dropdown != "仅使用模型":
            rag = RAG_class(model=model_dropdown, embed=vector_dropdown, c_name=chat_knowledge_base_dropdown, persist_directory=DB_directory)
            if chain_dropdown == "复杂召回方式":
                questions = rag.decomposition_chain(message)
                answer = rag.rag_chain(questions)
            elif chain_dropdown == "简单召回方式":
                answer = rag.simple_chain(message)
            else:
                answer = rag.rerank_chain(message)

        response = f" {answer}"
        chat_history.append(("Bot", response))
    return format_chat_history(chat_history), ""

def clear_chat():
    global chat_history
    chat_history = []
    return format_chat_history(chat_history)

def format_chat_history(history):
    formatted_history = ""
    for user, msg in history:
        if user == "User":
            formatted_history += f'''
            <div style="text-align: right; margin: 10px;">
                <div style="display: inline-block; background-color: #DCF8C6; padding: 10px; border-radius: 10px; max-width: 60%;">
                    {msg}
                </div>
                <b>:User</b>
            </div>
            '''
        else:
            if "```" in msg:  # 检测是否包含代码片段
                code_content = msg.split("```")[1]
                formatted_history += f'''
                <div style="text-align: left; margin: 10px;">
                    <b>Bot:</b>
                    <div style="display: inline-block; background-color: #F1F0F0; padding: 10px; border-radius: 10px; max-width: 60%;">
                        <pre><code>{code_content}</code></pre>
                    </div>
                </div>
                '''
            else:
                formatted_history += f'''
                <div style="text-align: left; margin: 10px;">
                    <b>Bot:</b>
                    <div style="display: inline-block; background-color: #F1F0F0; padding: 10px; border-radius: 10px; max-width: 60%;">
                        {msg}
                    </div>
                </div>
                '''
    return formatted_history

def clear_status():
    upload_status.update("")
    delete_status.update("")
    vectorize_status.update("")
    delete_collection_status.update("")

def handle_knowledge_base_selection(selected_knowledge_base):
    if selected_knowledge_base == "创建知识库":
        return gr.update(visible=True, interactive=True), gr.update(choices=[], value=[]), gr.update(visible=False)
    elif selected_knowledge_base == "仅使用模型":
        return gr.update(visible=False, interactive=False), gr.update(choices=[], value=[]), gr.update(visible=False)
    else:
        return gr.update(visible=False, interactive=False), search_knowledge_base(selected_knowledge_base), gr.update(visible=True)

def update_knowledge_base_dropdown():
    global knowledge_base_files
    choices = ["创建知识库"] + list(knowledge_base_files.keys())
    return gr.update(choices=choices)

def update_chat_knowledge_base_dropdown():
    global knowledge_base_files
    choices = ["仅使用模型"] + list(knowledge_base_files.keys())
    return gr.update(choices=choices)


# SearxNG搜索函数
def search_searxng(query):
    searxng_url = 'http://localhost:8080/search'  # 替换为你的SearxNG实例URL
    params = {
        'q': query,
        'format': 'json'
    }
    response = requests.get(searxng_url, params=params)
    response.raise_for_status()
    return response.json()


# Ollama总结函数
def summarize_with_ollama(model_dropdown,text, question):
    prompt = """
        根据下边的内容，回答用户问题，
        内容为：‘{0}‘\n
        问题为：{1}
    """.format(text, question)
    ollama_url = 'http://localhost:11434/api/generate'  # 替换为你的Ollama实例URL
    data = {
        'model': model_dropdown,
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(ollama_url, json=data)
    response.raise_for_status()
    return response.json()


# 处理函数
def ai_web_search(model_dropdown,user_query):
    # 使用SearxNG进行搜索
    search_results = search_searxng(user_query)
    search_texts = [result['title'] + "\n" + result['content'] for result in search_results['results']]
    combined_text = "\n\n".join(search_texts)

    # 使用Ollama进行总结
    summary = summarize_with_ollama(model_dropdown,combined_text, user_query)
    # print(summary)
    # 返回结果
    return summary['response']
# 添加新的函数来处理AI网络搜索
# def ai_web_search(model_dropdown, query):
#     try:
#         # 这里添加实际的网络搜索和AI处理逻辑
#         # 这只是一个示例，您需要根据实际情况实现
#         search_result = f"搜索结果: {query}"
#         ai_response = f"AI回答: 基于搜索结果，对于'{query}'的回答是..."
#         return f"{search_result}\n\n{ai_response}"
#     except Exception as e:
#         logger.error(f"Error in AI web search: {str(e)}")
#         return f"<div style='color: red;'>Error: {str(e)}</div>"

# 创建 Gradio 界面
with gr.Blocks() as demo:
    with gr.Column():
        # 添加标题
        title = gr.HTML("<h1 style='text-align: center; font-size: 32px; font-weight: bold;'>RAG精致系统</h1>")
        # 添加公告栏
        announcement = gr.HTML("<div style='text-align: center; font-size: 18px; color: red;'>公告栏: 欢迎使用RAG精致系统，一个适合学习、使用、自主扩展的【检索增强生成】系统！<br/>公众号：世界大模型</div>")

        with gr.Tabs():
            with gr.TabItem("知识库"):
                knowledge_base_dropdown = gr.Dropdown(choices=["创建知识库"] + list(knowledge_base_files.keys()),
                                                      label="选择知识库")
                new_kb_input = gr.Textbox(label="输入新的知识库名称", visible=False, interactive=True)
                file_input = gr.Files(label="Upload files")
                upload_btn = gr.Button("Upload")
                file_list = gr.CheckboxGroup(label="Uploaded Files")
                delete_btn = gr.Button("Delete Selected Files")
                with gr.Row():
                    chunk_size_dropdown = gr.Dropdown(choices=[50, 100, 200, 300, 500, 700], label="chunk_size", value=200)
                    chunk_overlap_dropdown = gr.Dropdown(choices=[20, 50, 100, 200], label="chunk_overlap", value=50)
                    vectorize_btn = gr.Button("Vectorize Selected Files")
                delete_collection_btn = gr.Button("Delete Collection")
                upload_status = gr.HTML()
                delete_status = gr.HTML()
                vectorize_status = gr.HTML()
                delete_collection_status = gr.HTML()

            with gr.TabItem("Chat"):
                with gr.Row():
                    model_dropdown = gr.Dropdown(choices=get_llm(), label="模型")
                    vector_dropdown = gr.Dropdown(choices=get_embeding_model(), label="向量")
                    chat_knowledge_base_dropdown = gr.Dropdown(choices=["仅使用模型"] + vectordb.get_all_collections_name(), label="知识库")
                    chain_dropdown = gr.Dropdown(choices=["复杂召回方式", "简单召回方式","rerank"], label="chain方式", visible=False)
                chat_display = gr.HTML(label="Chat History")
                chat_input = gr.Textbox(label="Type a message")
                chat_btn = gr.Button("Send")
                clear_btn = gr.Button("Clear Chat History")

            with gr.TabItem("AI网络搜索"):
                with gr.Row():
                    web_search_model_dropdown = gr.Dropdown(choices=get_llm(), label="模型")
                web_search_output = gr.Textbox(label="搜索结果和AI回答", lines=10)
                web_search_input = gr.Textbox(label="输入搜索查询")

                web_search_btn = gr.Button("搜索")

    def handle_upload(files):
        upload_result, new_files, status = upload_files(files)
        threading.Thread(target=clear_status).start()
        return upload_result, new_files, status, update_chat_knowledge_base_dropdown()

    def handle_delete(selected_knowledge_base, selected_files):
        tmp = []
        cols_files_tmp = vectordb.get_collcetion_content_files(c_name=selected_knowledge_base)
        for i in selected_files:
            if i in cols_files_tmp:
                tmp.append(i)
        del cols_files_tmp
        if tmp:
            vectordb.del_files(tmp, c_name=selected_knowledge_base)
        del tmp
        delete_result, status = delete_files(selected_files)
        threading.Thread(target=clear_status).start()
        return delete_result, status, update_chat_knowledge_base_dropdown()

    def handle_vectorize(selected_files, selected_knowledge_base, new_kb_name, chunk_size, chunk_overlap):
        vectorize_result, status = asyncio.run(async_vectorize_files(selected_files, selected_knowledge_base, new_kb_name, chunk_size, chunk_overlap))
        threading.Thread(target=clear_status).start()
        return vectorize_result, status, update_knowledge_base_dropdown(), update_chat_knowledge_base_dropdown()

    def handle_delete_collection(selected_knowledge_base):
        result, status = delete_collection(selected_knowledge_base)
        threading.Thread(target=clear_status).start()
        return result, status, update_chat_knowledge_base_dropdown()

    knowledge_base_dropdown.change(
        handle_knowledge_base_selection,
        inputs=knowledge_base_dropdown,
        outputs=[new_kb_input, file_list, chain_dropdown]
    )
    upload_btn.click(handle_upload, inputs=file_input, outputs=[file_list, file_list, upload_status, chat_knowledge_base_dropdown])
    delete_btn.click(handle_delete, inputs=[knowledge_base_dropdown, file_list], outputs=[file_list, delete_status, chat_knowledge_base_dropdown])
    vectorize_btn.click(handle_vectorize, inputs=[file_list, knowledge_base_dropdown, new_kb_input, chunk_size_dropdown, chunk_overlap_dropdown],
                        outputs=[gr.Textbox(visible=False), vectorize_status, knowledge_base_dropdown, chat_knowledge_base_dropdown])
    delete_collection_btn.click(handle_delete_collection, inputs=knowledge_base_dropdown,
                                outputs=[knowledge_base_dropdown, delete_collection_status, chat_knowledge_base_dropdown])

    chat_btn.click(chat_response, inputs=[model_dropdown, vector_dropdown, chat_knowledge_base_dropdown, chain_dropdown, chat_input], outputs=[chat_display, chat_input])
    clear_btn.click(clear_chat, outputs=chat_display)

    chat_knowledge_base_dropdown.change(
        fn=lambda selected: gr.update(visible=selected != "仅使用模型"),
        inputs=chat_knowledge_base_dropdown,
        outputs=chain_dropdown
    )

    # 添加新的点击事件处理
    web_search_btn.click(
        ai_web_search,
        inputs=[web_search_model_dropdown, web_search_input],
        outputs=web_search_output
    )

demo.launch(debug=True,share=True)