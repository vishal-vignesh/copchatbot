import cohere
import os

def generate_embedding(text):
    COHERE_API_KEY = os.getenv("COHERE_API_KEY")
    
    # Initialize Cohere client
    co = cohere.Client(COHERE_API_KEY)

    # Generate embedding for the input text
    response = co.embed(texts=[text], model="embed-english-v3.0", input_type="search_query")
    
    return response.embeddings[0]
