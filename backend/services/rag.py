import os
import time
from uuid import uuid4
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document


def initialize_pinecone_index(index_name, dimension=3072, metric="cosine", spec=None):
    """
    Initialize and return a Pinecone index. If the index does not exist, it is created and 
    the function waits until it is ready.
    
    Args:
        index_name (str): The name of the Pinecone index.
        dimension (int): The dimensionality of the vectors.
        metric (str): The distance metric (e.g., "cosine").
        spec (ServerlessSpec): The serverless spec configuration.
        
    Returns:
        A Pinecone Index object.
    """
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    pc = Pinecone(api_key=pinecone_api_key)
    existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]

    if index_name not in existing_indexes:
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric=metric,
            spec=spec,
        )
        while not pc.describe_index(index_name).status["ready"]:
            time.sleep(1)
    return pc.Index(index_name)


def create_vector_store(index):
    """
    Create and return a PineconeVectorStore instance using the provided index.
    
    Args:
        index: A Pinecone index object.
        
    Returns:
        A PineconeVectorStore instance.
    """
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    vector_store = PineconeVectorStore(index=index, embedding=embeddings)
    return vector_store


def create_documents():
    """
    Create and return a list of Document objects for demonstration.
    
    Returns:
        A list of Document instances.
    """
    documents = [
        Document(
            page_content="I had chocalate chip pancakes and scrambled eggs for breakfast this morning.",
            metadata={"source": "tweet"},
        ),
        Document(
            page_content="The weather forecast for tomorrow is cloudy and overcast, with a high of 62 degrees.",
            metadata={"source": "news"},
        ),
        Document(
            page_content="Building an exciting new project with LangChain - come check it out!",
            metadata={"source": "tweet"},
        ),
        Document(
            page_content="Robbers broke into the city bank and stole $1 million in cash.",
            metadata={"source": "news"},
        ),
        Document(
            page_content="Wow! That was an amazing movie. I can't wait to see it again.",
            metadata={"source": "tweet"},
        ),
        Document(
            page_content="Is the new iPhone worth the price? Read this review to find out.",
            metadata={"source": "website"},
        ),
        Document(
            page_content="The top 10 soccer players in the world right now.",
            metadata={"source": "website"},
        ),
        Document(
            page_content="LangGraph is the best framework for building stateful, agentic applications!",
            metadata={"source": "tweet"},
        ),
        Document(
            page_content="The stock market is down 500 points today due to fears of a recession.",
            metadata={"source": "news"},
        ),
        Document(
            page_content="I have a bad feeling I am going to get deleted :(",
            metadata={"source": "tweet"},
        ),
    ]
    return documents


def main():
    """
    Main demonstration function that initializes the Pinecone vector store, adds documents,
    performs deletion, and executes similarity searches.
    """
    load_dotenv()  # Load environment variables from .env

    index_name = "conv-ai"
    spec = ServerlessSpec(cloud="aws", region="us-east-1")
    index = initialize_pinecone_index(index_name, dimension=3072, metric="cosine", spec=spec)
    vector_store = create_vector_store(index)

    # Create and add documents to the vector store
    documents = create_documents()
    uuids = [str(uuid4()) for _ in range(len(documents))]
    vector_store.add_documents(documents=documents, ids=uuids)

    # Delete the last document
    vector_store.delete(ids=[uuids[-1]])

    # Perform a similarity search for documents with source 'tweet'
    results = vector_store.similarity_search(
        "LangChain provides abstractions to make working with LLMs easy",
        k=2,
        filter={"source": "tweet"},
    )
    for res in results:
        print(f"* {res.page_content} [{res.metadata}]")

    # Perform a similarity search with score for documents with source 'news'
    results_with_score = vector_store.similarity_search_with_score(
        "Will it be hot tomorrow?", k=1, filter={"source": "news"}
    )
    for res, score in results_with_score:
        print(f"* [SIM={score:3f}] {res.page_content} [{res.metadata}]")


if __name__ == "__main__":
    main()
