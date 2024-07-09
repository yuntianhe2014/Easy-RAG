# Easy-RAG
一个适合学习、使用、自主扩展的RAG【检索增强生成】系统！

1、目前已有的功能

    知识库（目前仅支持txt\csv\pdf格式数据）：

        1、知识库的创建

        2、知识库的更新

        3、删除知识库中某个文件

        4、删除知识库

        5、向量化知识库

    chat

        1、支持纯大模型聊天多伦

        2、支持知识库问答

2、后续更新计划

    知识库：

        0、支持FAISS，Elasticsearch、Milvus等向量数据

        1、支持音频和视频的解析入库向量化

        2、支持md、json、excel、docs等数据格式（大家可以自己去试试添加，so easy）

    chat：

        1、添加 语音回答输出

安装使用
  Ollma安装，在如下网址选择适合你机器的ollama 安装包，傻瓜式安装即可
  
    https://ollama.com/download
  Ollama 安装模型，本次直接安装我们需要的两个 cmd中执行
  
    ollama run qwen2:7b
    ollama run mofanke/acge_text_embedding:latest
  项目开发使用的 python3.10.9  经测试 pyhon3.8以上皆可使用
  
    git clone https://github.com/yuntianhe2014/Easy-RAG.git
  安装依赖
  
    pip3 install -r requirements.txt -i  https://mirrors.aliyun.com/pypi/simple
  项目启动
  
    python webui.py

更多介绍参考 公众号文章：世界大模型
![img](wx.png)


