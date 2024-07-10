from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.document_loaders import TextLoader,UnstructuredCSVLoader, UnstructuredPDFLoader,UnstructuredWordDocumentLoader,UnstructuredExcelLoader,UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from .asr_utils import get_spk_txt

class ChromaDB():
    def __init__(self, embedding="mofanke/acge_text_embedding:latest", persist_directory="./Chroma_db/"):

        self.embedding = OllamaEmbeddings(model=embedding)
        self.persist_directory = persist_directory
        self.chromadb = Chroma(persist_directory=persist_directory)
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=50)

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

        vectorstore = self.chromadb.from_documents(documents=splits, collection_name=c_name,
                                                   embedding=self.embedding, persist_directory=self.persist_directory)
        print("数据块总量:", vectorstore._collection.count())

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

        vectorstore = Chroma(persist_directory=self.persist_directory, collection_name=c_name,
                             embedding_function=self.embedding)
        vectorstore.add_documents(splits)
        print("数据块总量:", vectorstore._collection.count())

        return vectorstore

    # 删除 某个collection中的 某个文件
    def del_files(self, del_files_name, c_name):

        vectorstore = self.chromadb._client.get_collection(c_name)
        del_ids = []
        vec_dict = vectorstore.get()
        for id, md in zip(vec_dict["ids"], vec_dict["metadatas"]):
            for dl in del_files_name:
                if dl in md["source"]:
                    del_ids.append(id)
        vectorstore.delete(ids=del_ids)
        print("数据块总量:", vectorstore.count())

        return vectorstore

    # 删除某个 知识库 collection
    def delete_collection(self, c_name):

        self.chromadb._client.delete_collection(c_name)

    # 获取目前所有 collection
    def get_all_collections_name(self):
        cl_names = []

        test = self.chromadb._client.list_collections()
        for i in range(len(test)):
            cl_names.append(test[i].name)
        return cl_names

    # 获取 collection中的所有文件
    def get_collcetion_content_files(self, c_name):
        vectorstore = self.chromadb._client.get_collection(c_name)
        c_files = []
        vec_dict = vectorstore.get()
        for md in vec_dict["metadatas"]:
            c_files.append(md["source"])
        return list(set(c_files))


# if __name__ == "__main__":
#     chromadb = ChromaDB()
#     c_name = "sss3"
#
#     print(chromadb.get_all_collections_name())
#     chromadb.create_collection(["data/肾内科学.txt", "data/jl.pdf"], c_name=c_name)
#     print(chromadb.get_all_collections_name())
#     chromadb.add_chroma(["data/儿科学.txt"], c_name=c_name)
#     print(c_name, "包含的文件:", chromadb.get_collcetion_content_files(c_name))
#     chromadb.del_files(["data/肾内科学.txt"], c_name=c_name)
#     print(c_name, "包含的文件:", chromadb.get_collcetion_content_files(c_name))
#     print(chromadb.get_all_collections_name())
#     chromadb.delete_collection(c_name=c_name)
#     print(chromadb.get_all_collections_name())