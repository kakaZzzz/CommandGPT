from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

class VectorDB():
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.db = Chroma(
            collection_name="test",
            embedding_function=self.embeddings,
            persist_directory="library/db"
        )

    def add(self, text, name):
        res = self.db.add_texts(
            texts=[text],
            ids=[name],
            metadatas=[{"name": name}]
        )
        return res

    def search(self, text, k=1):
        res = self.db.similarity_search_with_score(text, k=k)
        return res

    def delete(self):
        res = self.db.delete_collection()
        return res

    def update(self, text, name):
        res = self.db.update_text(text, name)
        return res