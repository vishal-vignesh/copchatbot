import cohere
from pinecone import (
    Pinecone,
    ServerlessSpec,
    CloudProvider,
    AwsRegion,
    VectorType
)
from tqdm.auto import tqdm
from datasets import load_dataset
import os
# Set your API keys
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
# Load the dataset
dataset = load_dataset("viber1/indian-law-dataset", split="train")
data = dataset.to_pandas()  # Convert to pandas DataFrame for easier processing

# Initialize Cohere client
co = cohere.Client(COHERE_API_KEY)

# Initialize Pinecone client using your specified syntax
pc = Pinecone(api_key=PINECONE_API_KEY, environment="us-east-1")
INDEX_NAME = "legal-chatbot-index-1024"

# Create a new Pinecone index if it doesn't already exist
# index_config = pc.create_index(
#     name=INDEX_NAME,
#     dimension=1536,
#     spec=ServerlessSpec(
#         cloud=CloudProvider.AWS,
#         region=AwsRegion.US_EAST_1
#     ),
#     vector_type=VectorType.DENSE
# )

# Connect to the Pinecone index
index = pc.Index("legal-chatbot-index-1024")

# Process and upsert in batches
batch_size = 50  # Adjust based on system memory
for i in tqdm(range(0, len(data), batch_size)):
    i_end = min(len(data), i + batch_size)
    batch = data.iloc[i:i_end]

    # Use the 'Instruction' column for embedding
    texts = batch['Instruction'].tolist()  # Ensure 'Instruction' is a valid column

    # Generate embeddings using Cohere
    response = co.embed(texts=texts, model="embed-english-v3.0", input_type="search_document")
    embeddings = response.embeddings

    # Prepare records for upsertion
    records = []
    for idx, (_, row) in enumerate(batch.iterrows()):
        record = {
            "id": f"doc_{i + idx}",
            "values": embeddings[idx],
            "metadata": {
                "instruction": row['Instruction'],  # Store the instruction text as metadata
                "response": row['Response']         # Store the response text as metadata
            }
        }
        records.append(record)

    # Upsert records into Pinecone index
    index.upsert(vectors=records)

print("Data successfully upserted into Pinecone!")

# Query function to test the index
# def query_index(query_text, top_k=3):
#     # Generate embedding for the query text using Cohere
#     query_embedding = co.embed(texts=[query_text], model="embed-english-v3.0", input_type="search_query").embeddings[0]

#     # Query Pinecone index
#     results = index.query(
#         vector=query_embedding,
#         top_k=top_k,
#         include_metadata=True
#     )

#     return results

# # Test the system with a query
# test_query = "How do I file an FIR?"
# results = query_index(test_query)

# # Print results
# print("\nTest Query Results:")
# for match in results['matches']:
#     print(f"\nScore: {match['score']}")
#     print(f"Question: {match['metadata']['instruction']}")
#     print(f"Answer: {match['metadata']['response']}")
