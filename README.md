# Easy-RAG
一个适合学习、使用、自主扩展的RAG【检索增强生成】系统，可以联网做AI搜索！


![img](https://github.com/yuntianhe2014/Easy-RAG/blob/main/img/zhu.png)

更新历史

        2024/9/04 增加 AI网络搜索 可以联网查询
        2024/9/04 优化webui异步调用，提高响应速度
        2024/8/21 增加对 Elasticsearch 支持，在config中设置
        2024/7/23 参考 meet-libai 项目增加了一个知识图谱的时时提取工具，目前仅是提取，未存储 graph_demo_ui.py
        2024/7/11 新增faiss向量数据库支持，目前支持(Chroma\FAISS)
        2024/7/10 更新rerank搜索方式
        2024/7/09 第一版发布
![img](https://github.com/yuntianhe2014/Easy-RAG/blob/main/img/zhuye.png)

1、目前已有的功能

    知识库（目前仅支持txt\csv\pdf\md\doc\docx\mp3\mp4\wav\excel\格式数据）：

        1、知识库的创建（目前仅支持Chroma\Faiss\Elasticsearch）
        2、知识库的更新
        3、删除知识库中某个文件
        4、删除知识库
        5、向量化知识库
        6、支持音频视频的语音转文本然后向量化 
            语音转文本 使用的 funasr ，第一次启动时，会从魔塔下载模型，可能会慢一些，之后会自动加载模型

    chat

        1、支持纯大模型聊天多轮
        2、支持知识库问答 ["复杂召回方式", "简单召回方式","rerank"]
        
    AI网络搜索
        
        支持网络搜素，大家可以优化 prompt 增加不同 程度的 总结
        llm基于ollama可以选择不同模型
        注意：联网基于 searxng，需要先本地或者服务启动 这个项目，我用docker 启动的
        参考 https://github.com/searxng/searxng-docker
        
![img](https://github.com/yuntianhe2014/Easy-RAG/blob/main/img/复杂方式.png)
        3、通过使用rerank重新排序来提高检索效率
        
        本次rerank 使用了bge-reranker-large 模型，需要下载到本地，然后再 rag/rerank.py中配置路径
            模型地址：https://hf-mirror.com/BAAI/bge-reranker-large
     

2、后续更新计划

    知识库：

        0、支持Elasticsearch、Milvus,MongoDB等向量数据


    chat：

        1、添加 语音回答输出
        2、增加 问题路由知识库的 功能
        

安装使用

       Ollma安装，在如下网址选择适合你机器的ollama 安装包，傻瓜式安装即可
      
        https://ollama.com/download
      Ollama 安装模型，本次直接安装我们需要的两个 cmd中执行
      
        ollama run qwen2:7b
        ollama run mofanke/acge_text_embedding:latest
       
      下载bge-reranker-large 模型然后在 rag/rerank.py中配置路径
        
        https://hf-mirror.com/BAAI/bge-reranker-large
        
      选择你想使用的向量数据库 目前仅支持（Chroma和Faiss）
      
        在 Config/config.py中配置你想用的 向量数据库
        如果选择 Elasticsearch 请先启动 Elasticsearch，我是使用docker 启动的
           docker run -p 9200:9200 -e "discovery.type=single-node" -e "xpack.security.enabled=false" -e "xpack.security.http.ssl.enabled=false" docker.elastic.co/elasticsearch/elasticsearch:8.12.1
        注意修改 es_url
        
      构造python环境
      
        conda create -n Easy-RAG python=3.10.9
        conda activate Easy-RAG
        
      项目开发使用的 python3.10.9  经测试 pyhon3.8以上皆可使用
      
        git clone https://github.com/yuntianhe2014/Easy-RAG.git
      安装依赖
      
        pip3 install -r requirements.txt -i  https://mirrors.aliyun.com/pypi/simple
       
      部署依赖联网项目searxng
        参考 https://github.com/searxng/searxng-docker
      项目启动
      
        python webui.py
        
      知识图谱时时提取工具
        python graph_demo_ui.py
  ![img](https://github.com/yuntianhe2014/Easy-RAG/blob/main/img/graph-tool.png)

更多介绍参考 公众号文章：世界大模型
![img](https://github.com/yuntianhe2014/Easy-RAG/blob/main/img/%E5%BE%AE%E4%BF%A1%E5%9B%BE%E7%89%87_20240524180648.jpg)

项目参考：
    https://github.com/BinNong/meet-libai
    https://github.com/searxng/searxng-docker
