from pinecone import (
    Pinecone,
    ServerlessSpec,
)
import os

def get_pinecone_index():
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    INDEX_NAME = "legal-chatbot-index-1024"

    # Initialize Pinecone client
    pc = Pinecone(api_key=PINECONE_API_KEY)

    # Connect to the existing index
    index = pc.Index(INDEX_NAME)
    
    return index
