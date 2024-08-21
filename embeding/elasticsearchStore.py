from elasticsearch import Elasticsearch
from langchain_elasticsearch.vectorstores import ElasticsearchStore
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.document_loaders import TextLoader, UnstructuredCSVLoader, UnstructuredPDFLoader, \
    UnstructuredWordDocumentLoader, UnstructuredExcelLoader, UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from .asr_utils import get_spk_txt
import requests


class ElsStore():
    def __init__(self, embedding="mofanke/acge_text_embedding:latest", es_url="http://localhost:9200",
                 index_name='test_index'):
        self.embedding = OllamaEmbeddings(model=embedding)
        self.es_url = es_url
        self.elastic_vector_search = ElasticsearchStore(
            es_url=self.es_url,
            index_name=index_name,
            embedding=self.embedding
        )

    def parse_data(self, file):
        if "txt" in file.lower() or "csv" in file.lower():
            try:
                loaders = UnstructuredCSVLoader(file)
                data = loaders.load()
            except:
                loaders = TextLoader(file, encoding="utf-8")
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

    def get_count(self, c_name):
        # 获取index-anme中的数据块数

        # 初始化 Elasticsearch 客户端
        es = Elasticsearch([{
            'host': self.es_url.split(":")[1][2:],
            'port': int(self.es_url.split(":")[2]),
            'scheme': 'http'  # 指定使用的协议
        }])

        # 指定索引名称
        index_name = c_name

        # 获取文档总数
        response = es.count(index=index_name)

        # 输出文档总数
        return response['count']

    # 创建 新的index_name 并且初始化
    def create_collection(self, files, c_name, chunk_size=200, chunk_overlap=50):
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        print("开始创建数据库 ....")
        tmps = []
        for file in files:
            data = self.parse_data(file)
            tmps.extend(data)

        splits = self.text_splitter.split_documents(tmps)

        self.elastic_vector_search = ElasticsearchStore.from_documents(
            documents=splits,
            embedding=self.embedding,
            es_url=self.es_url,
            index_name=c_name,
        )

        self.elastic_vector_search.client.indices.refresh(index=c_name)

        print("数据块总量:", self.get_count(c_name))

        return self.elastic_vector_search

    # 添加 数据到已有数据库
    def add_chroma(self, files, c_name, chunk_size=200, chunk_overlap=50):
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        print("开始添加文件...")
        tmps = []
        for file in files:
            data = self.parse_data(file)
            tmps.extend(data)

        splits = self.text_splitter.split_documents(tmps)

        self.elastic_vector_search = ElasticsearchStore(
            es_url=self.es_url,
            index_name=c_name,
            embedding=self.embedding
        )
        self.elastic_vector_search.add_documents(splits)
        self.elastic_vector_search.client.indices.refresh(index=c_name)
        print("数据块总量:", self.get_count(c_name))

        return self.elastic_vector_search

    # 删除某个 知识库 collection
    def delete_collection(self, c_name):
        url = self.es_url + "/" + c_name
        # 发送 DELETE 请求
        response = requests.delete(url)

        # 检查响应状态码
        if response.status_code == 200:
            return f"索引 'test-basic1' 已成功删除。"
        elif response.status_code == 404:
            return f"索引 'test-basic1' 不存在。"
        else:
            return f"删除索引时出错: {response.status_code}, {response.text}"

    # 获取目前所有 index_names
    def get_all_collections_name(self):
        indices = self.elastic_vector_search.client.indices.get_alias()
        index_names = list(indices.keys())

        return index_names

    def get_collcetion_content_files(self,c_name):
        return []

    # 删除 某个collection中的 某个文件
    def del_files(self, del_files_name, c_name):
        return None


