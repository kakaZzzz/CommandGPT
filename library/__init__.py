# !/usr/bin/env python3
"""This module is a template

Author:
Date:
Last modified:
Filename:
"""
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
import app.functions as f


class VectorDB():
    """

    """
    def __init__(self):
        """

        """
        self.embeddings = OpenAIEmbeddings()
        self.db = Chroma(
            collection_name="command",
            embedding_function=self.embeddings,
            persist_directory="library/db"
        )

    def add(self, text, name):
        """

        @param text:
        @param name:
        @return:
        """
        res = self.db.add_texts(
            texts=[text],
            ids=[name],
            metadatas=[{"name": name}]
        )

        return res

    def search(self, text, k=1):
        """

        @param text:
        @param k:
        @return:
        """
        res = self.db.similarity_search_with_score(text, k=k)
        return res

    def delete_by_ids(self, ids):
        """

        @param ids:
        @return:
        """
        res = self.db._collection.delete(ids)
        return res

    def get_by_id(self, ids):
        """

        @param ids:
        @return:
        """
        res = self.db._collection.get(ids)
        return res

    def get(self):
        """

        @return:
        """
        res = self.db._collection.get()
        return res

    def update(self, text, name):
        """

        @param text:
        @param name:
        @return:
        """
        res = self.db.update_text(text, name)
        return res

    def delete_collection(self):
        """

        @return:
        """
        res = self.db.delete_collection()
        return res
