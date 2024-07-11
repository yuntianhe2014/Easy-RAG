from langchain_community.vectorstores import Chroma,FAISS
from langchain_community.llms import Ollama
from langchain_core.output_parsers import StrOutputParser
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.runnables import RunnablePassthrough
from operator import itemgetter
from langchain.prompts import ChatPromptTemplate
from .rerank import rerank_topn
from Config.config import VECTOR_DB,DB_directory


class RAG_class:
    def __init__(self, model="qwen2:7b", embed="mofanke/acge_text_embedding:latest", c_name="sss1",
                 persist_directory="./Chroma_db/"):
        template = """
        根据上下文回答以下问题,不要自己发挥，要根据以下参考内容总结答案，如果以下内容无法得到答案，就返回无法根据参考内容获取答案，

        参考内容为：{context}

        问题: {question}
        """

        self.prompts = ChatPromptTemplate.from_template(template)

        # 使用 问题扩展+结果递归方式得到最终答案
        template1 = """你是一个乐于助人的助手，可以生成与输入问题相关的多个子问题。
        目标是将输入分解为一组可以单独回答的子问题/子问题。
        生成多个与以下内容相关的搜索查询：{question}
        输出4个相关问题,以换行符隔开："""
        self.prompt_questions = ChatPromptTemplate.from_template(template1)

        # 构建 问答对
        template2 = """
        以下是您需要回答的问题：

        \n--\n {question} \n---\n

        以下是任何可用的背景问答对：

        \n--\n {q_a_pairs} \n---\n

        以下是与该问题相关的其他上下文：

        \n--\n {context} \n---\n

        使用以上上下文和背景问答对来回答问题，问题是：{question} ，答案是：
        """
        self.decomposition_prompt = ChatPromptTemplate.from_template(template2)

        self.llm = Ollama(model=model)
        self.embeding = OllamaEmbeddings(model=embed)
        try:
            if VECTOR_DB==1:
                self.vectstore = Chroma(embedding_function=self.embeding, collection_name=c_name,
                                    persist_directory=persist_directory)
            elif VECTOR_DB ==2:
                self.vectstore = FAISS.load_local(folder_path=persist_directory + c_name, embeddings=self.embeding,
                                               allow_dangerous_deserialization=True)
            self.retriever = self.vectstore.as_retriever()
        except:
            print("仅模型时无需加载数据库")
    #
    # Post-processing
    def format_docs(self,docs):
        return "\n\n".join(doc.page_content for doc in docs)
    # 传统方式召回，单问题召回，然后llm总结答案回答
    def simple_chain(self,question):
        _chain = (
            {"context": self.retriever|self.format_docs,"question":RunnablePassthrough()}
            |self.prompts
            |self.llm
            |StrOutputParser()
        )
        answer = _chain.invoke({"question":question})
        return answer

    def rerank_chain(self,question):
        retriever = self.vectstore.as_retriever(search_kwargs={"k": 10})
        docs = retriever.invoke(question)
        docs = rerank_topn(question,docs,N=5)
        _chain = (
                self.prompts
                | self.llm
                | StrOutputParser()
        )
        answer = _chain.invoke({"context":self.format_docs(docs),"question": question})
        return answer

    def format_qa_pairs(self, question, answer):
        formatted_string = ""
        formatted_string += f"Question: {question}\nAnswer:{answer}\n\n"
        return formatted_string

    # 获取问题的 扩展问题
    def decomposition_chain(self, question):
        _chain = (
                {"question": RunnablePassthrough()}
                | self.prompt_questions
                | self.llm
                | StrOutputParser()
                | (lambda x: x.split("\n"))
        )

        questions = _chain.invoke({"question": question}) + [question]

        return questions
    # 多问题递归召回，每次召回后，问题和答案同时作为下一次召回的参考，再次用新问题召回
    def rag_chain(self, questions):
        q_a_pairs = ""
        for q in questions:
            _chain = (
                    {"context": itemgetter("question") | self.retriever,
                     "question": itemgetter("question"),
                     "q_a_pairs": itemgetter("q_a_paris")
                     }
                    | self.decomposition_prompt
                    | self.llm
                    | StrOutputParser()
            )

            answer = _chain.invoke({"question": q, "q_a_paris": q_a_pairs})
            q_a_pairs = self.format_qa_pairs(q, answer)
            q_a_pairs = q_a_pairs + "\n----\n" + q_a_pairs
        return answer

    # 将聊天历史格式化为一个字符串
    def format_chat_history(self,history):
        formatted_history = ""
        for role,content in history:
            formatted_history += f"{role}: {content}\n"
        return formatted_history
    # 基于ollama大模型的大模型 多轮对话，不使用知识库的
    def mult_chat(self,chat_history):
        # 格式化聊天历史
        formatted_history = self.format_chat_history(chat_history)

        # 调用模型生成回复
        response = self.llm.invoke(formatted_history)
        return response



# if __name__ == "__main__":
#     rag = RAG_class(model="gemma2:9b")
#     question = "人卫社官网网址是？"
#     questions = rag.decomposition_chain(question)
#     print(questions)
#     answer = rag.rag_chain(questions)
#     print(answer)