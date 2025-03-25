import os
import time
from uuid import uuid4
from typing import List, Optional
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document

class RAGSystem:
    def __init__(
        self,
        index_name: str,
        dimension: int = 3072,
        metric: str = "cosine",
        cloud: str = "aws",
        region: str = "us-east-1"
    ):
        load_dotenv()
        self.index_name = index_name
        self.dimension = dimension
        self.metric = metric
        self.spec = ServerlessSpec(cloud=cloud, region=region)

        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.pc = Pinecone(api_key=self.pinecone_api_key)

        self.index = self._initialize_index()
        self.vector_store = PineconeVectorStore(index=self.index, embedding=OpenAIEmbeddings(model="text-embedding-3-large"))

    def _initialize_index(self):
        existing_indexes = [i["name"] for i in self.pc.list_indexes()]
        if self.index_name not in existing_indexes:
            self.pc.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric=self.metric,
                spec=self.spec,
            )
            while not self.pc.describe_index(self.index_name).status["ready"]:
                time.sleep(1)
        return self.pc.Index(self.index_name)

    def add_documents(self, documents: List[Document]) -> List[str]:
        ids = [str(uuid4()) for _ in documents]
        self.vector_store.add_documents(documents=documents, ids=ids)
        return ids

    def delete_documents(self, ids: List[str]):
        self.vector_store.delete(ids=ids)

    def similarity_search(self, query: str, k: int = 2, metadata_filter: Optional[dict] = None) -> List[Document]:
        return self.vector_store.similarity_search(query, k=k, filter=metadata_filter)

    def similarity_search_with_score(self, query: str, k: int = 1, metadata_filter: Optional[dict] = None, score_threshold: float = 0.3):
        results_with_score = self.vector_store.similarity_search_with_score(query, k=k, filter=metadata_filter)
        # Filter out documents with a score below the threshold
        filtered_results = [(doc, score) for doc, score in results_with_score if score >= score_threshold]
        
        return filtered_results


    def create_document_from_text(self, text: str, metadata: Optional[dict] = None) -> Document:
        return Document(page_content=text, metadata=metadata or {})

    def create_documents_from_file(self, file_path: str, metadata: Optional[dict] = None) -> List[Document]:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return [Document(page_content=content, metadata=metadata or {"source": os.path.basename(file_path)})]


def main():
    rag = RAGSystem(index_name="conv-ai")

    # Perform similarity search
    results = rag.similarity_search_with_score(
        "How is the weather today?",
        k=1,
    )
    
if __name__ == "__main__":
    main()
