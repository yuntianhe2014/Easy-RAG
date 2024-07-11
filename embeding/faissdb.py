from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.document_loaders import TextLoader,UnstructuredCSVLoader, UnstructuredPDFLoader,UnstructuredWordDocumentLoader,UnstructuredExcelLoader,UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import shutil
import os
from .asr_utils import get_spk_txt


class FaissDB():
    def __init__(self, embedding="mofanke/acge_text_embedding:latest", persist_directory="./Faiss_db/"):

        self.embedding = OllamaEmbeddings(model=embedding)
        self.persist_directory = persist_directory
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50, add_start_index=True)

    def parse_data(self,file):
        if "txt" in file.lower() or "csv" in file.lower():
            try:
                loaders = UnstructuredCSVLoader(file)
                data = loaders.load()
            except:
                loaders = TextLoader(file,encoding="utf-8")
                data = loaders.load()
        if ".doc" in file.lower() or ".docx" in file.lower():
            loaders = UnstructuredWordDocumentLoader(file)
            data = loaders.load()
        if "pdf" in file.lower():
            loaders = UnstructuredPDFLoader(file)
            data = loaders.load()
        if ".xlsx" in file.lower():
            loaders = UnstructuredExcelLoader(file)
            data = loaders.load()
        if ".md" in file.lower():
            loaders = UnstructuredMarkdownLoader(file)
            data = loaders.load()
        if "mp3" in file.lower() or "mp4" in file.lower() or "wav" in file.lower():
            # 语音解析成文字
            fw = get_spk_txt(file)
            loaders = UnstructuredCSVLoader(fw)
            data = loaders.load()
            tmp = []
            for i in data:
                i.metadata["source"] = file
                tmp.append(i)
            data = tmp
        return data

    # 创建 新的collection 并且初始化
    def create_collection(self, files, c_name,chunk_size=200, chunk_overlap=50):
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        print("开始创建数据库 ....")
        tmps = []
        for file in files:
            data = self.parse_data(file)
            tmps.extend(data)

        splits = self.text_splitter.split_documents(tmps)

        vectorstore = FAISS.from_documents(documents=splits,
                                           embedding=self.embedding)
        vectorstore.save_local(self.persist_directory + c_name)
        print("数据块总量:", vectorstore.index.ntotal)

        return vectorstore

    # 添加 数据到已有数据库
    def add_chroma(self, files, c_name,chunk_size=200, chunk_overlap=50):
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        print("开始添加文件...")
        tmps = []
        for file in files:
            data = self.parse_data(file)
            tmps.extend(data)

        splits = self.text_splitter.split_documents(tmps)

        vectorstore = FAISS.load_local(folder_path=self.persist_directory + c_name, embeddings=self.embedding,
                                       allow_dangerous_deserialization=True)
        vectorstore.add_documents(documents=splits)
        vectorstore.save_local("Faiss_db/" + c_name)
        print("数据块总量:", vectorstore.index.ntotal)

        return vectorstore

    # 删除 某个collection中的 某个文件
    def del_files(self, del_files_name, c_name):

        vectorstore = FAISS.load_local(folder_path=self.persist_directory + c_name, embeddings=self.embedding,
                                       allow_dangerous_deserialization=True)
        del_ids = []
        vec_dict = vectorstore.docstore._dict
        for id, md in vec_dict.items():
            for dl in del_files_name:
                if dl in md.metadata["source"]:
                    del_ids.append(id)
        vectorstore.delete(ids=del_ids)
        vectorstore.save_local(self.persist_directory + c_name)
        print("数据块总量:", vectorstore.index.ntotal)

        return vectorstore

    # 删除某个 知识库 collection
    def delete_collection(self, c_name):
        shutil.rmtree(self.persist_directory + c_name)

    # 获取目前所有 collection
    def get_all_collections_name(self):
        cl_names = [i for i in os.listdir(self.persist_directory) if os.path.isdir(self.persist_directory+i)]

        return cl_names

    # 获取 collection中的所有文件
    def get_collcetion_content_files(self, c_name):
        vectorstore = FAISS.load_local(folder_path=self.persist_directory + c_name, embeddings=self.embedding,
                                       allow_dangerous_deserialization=True)
        c_files = []
        vec_dict = vectorstore.docstore._dict
        for _, md in vec_dict.items():
            c_files.append(md.metadata["source"])

        return list(set(c_files))


# if __name__ == "__main__":
#     chromadb = FaissDB()
#     c_name = "sss3"
#
#     print(chromadb.get_all_collections_name())
#     chromadb.create_collection(["data/jl.txt", "data/jl.pdf"], c_name=c_name)
#     print(chromadb.get_all_collections_name())
#     chromadb.add_chroma(["data/tmp.txt"], c_name=c_name)
#     print(c_name, "包含的文件:", chromadb.get_collcetion_content_files(c_name))
#     chromadb.del_files(["data/tmp.txt"], c_name=c_name)
#     print(c_name, "包含的文件:", chromadb.get_collcetion_content_files(c_name))
#     print(chromadb.get_all_collections_name())
#     chromadb.delete_collection(c_name=c_name)
#     print(chromadb.get_all_collections_name())