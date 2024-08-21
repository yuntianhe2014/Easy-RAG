from py2neo import Graph, Node, Relationship
from langchain_community.document_loaders import TextLoader,UnstructuredCSVLoader, UnstructuredPDFLoader,UnstructuredWordDocumentLoader,UnstructuredExcelLoader,UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter



class KnowledgeGraph:
    def __init__(self, uri, user, password):
        self.graph = Graph(uri, auth=(user, password))

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
        return data

    # 切分 数据
    def split_files(self, files,chunk_size=500, chunk_overlap=100):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        print("开始创建数据库 ....")
        tmps = []
        for file in files:
            data = self.parse_data(file)
            tmps.extend(data)

        splits = text_splitter.split_documents(tmps)

        return splits

    def create_node(self, label, properties):
        matcher = self.graph.nodes.match(label, **properties)
        if matcher.first():
            return matcher.first()
        else:
            node = Node(label, **properties)
            self.graph.create(node)
            return node

    def create_relationship(self, label1, properties1, label2, properties2, relationship_type,
                            relationship_properties={}):
        node1 = self.create_node(label1, properties1)
        node2 = self.create_node(label2, properties2)

        matcher = self.graph.match((node1, node2), r_type=relationship_type)
        for rel in matcher:
            if all(rel[key] == value for key, value in relationship_properties.items()):
                return rel

        relationship = Relationship(node1, relationship_type, node2, **relationship_properties)
        self.graph.create(relationship)
        return relationship

    def delete_node(self, label, properties):
        matcher = self.graph.nodes.match(label, **properties)
        node = matcher.first()
        if node:
            self.graph.delete(node)
            return True
        return False

    def update_node(self, label, identifier, updates):
        matcher = self.graph.nodes.match(label, **identifier)
        node = matcher.first()
        if node:
            for key, value in updates.items():
                node[key] = value
            self.graph.push(node)
            return node
        return None

    def find_node(self, label, properties):
        matcher = self.graph.nodes.match(label, **properties)
        return list(matcher)

    def create_nodes(self, label, properties_list):
        nodes = []
        for properties in properties_list:
            node = self.create_node(label, properties)
            nodes.append(node)
        return nodes

    def create_relationships(self, relationships):
        created_relationships = []
        for rel in relationships:
            label1, properties1, label2, properties2, relationship_type = rel
            relationship = self.create_relationship(label1, properties1, label2, properties2, relationship_type)
            created_relationships.append(relationship)
        return created_relationships

