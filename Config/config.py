# 向量数据库选择 【chroma：1】 ，【faiss 2】,【ElasticsearchStore 3】
VECTOR_DB = 3
DB_directory = "./Chroma_db/"
if VECTOR_DB==2:
    DB_directory ="./Faiss_db/"
elif VECTOR_DB==3:
    DB_directory = "es"

# 配置neo4j
neo4j_host = "bolt://localhost:7687"
neo4j_name = "neo4j"
neo4j_pwd = "12345678"
# 测试了 llama3：8b,gemma2:9b,qwen2:7b,glm4:9b，arcee-ai/arcee-agent:latest  目前来看 qwen2:7 效果最好
neo4j_model = "qwen2:7b"