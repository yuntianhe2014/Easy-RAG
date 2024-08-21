# -*- coding: utf-8 -*-
import sys
sys.path.append(r"..//")#
from Neo4j.neo4j_op import KnowledgeGraph
from Neo4j.graph_extract import update_graph
from Config.config import neo4j_host,neo4j_name,neo4j_pwd



kg = KnowledgeGraph(neo4j_host,neo4j_name,neo4j_pwd)


if __name__ == "__main__":

    text = """范冰冰，1981年9月16日生于山东青岛，毕业于上海师范大学谢晋影视艺术学院，中国女演员，歌手。 
    1998年参演电视剧《还珠格格》成名。2004年主演电影《手机》获得第27届大众电影百花奖最佳女演员奖。"""
    res = update_graph(text)
    # 批量创建节点
    nodes = kg.create_nodes("node", res["nodes"])
    print(nodes)
    # 批量创建关系
    relationships = kg.create_relationships([
        ("node", {"name": edge["source"]}, "node", {"name": edge["target"]}, edge["label"]) for edge in res["edges"]
    ])
    print(relationships)