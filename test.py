import re
import app.functions as f
import os
import requests
import platform
import chromadb

from langchain.vectorstores import Chroma

envs = f.load_env()
os.environ["OPENAI_API_KEY"] = envs["OPENAI_API_KEY"]

s = """
根据输出信息可以看出，执行命令pip --version成功，且返回了版本信息。returncode为0表示命令执行成功。因此，命令执行成功。

按照要求，返回结果为：
{
    "result": "success",
    "reasoning": "Command 'pip --version' executed successfully and returned version information"
}
"""

matchObj = re.search( r'(\{.*\})', s, re.M|re.I|re.S)

# print(matchObj[0])

from langchain.embeddings import OpenAIEmbeddings

text = """
{{
    "goal": "帮我安装pytoch",
}}
"""
name = "skill3"

embeddings = OpenAIEmbeddings()
# query_result = embeddings.embed_query(text)
db = Chroma(
    collection_name="test",
    embedding_function=embeddings,
    persist_directory="library/db"
)
# res = db.add_texts(
#     texts=[text],
#     ids=[name],
#     metadatas=[{"name": name}]
# )

t1 = "帮我安装pytorch"

res1 = db.similarity_search_with_score(t1)
print(res1)