from flask import Flask, request, jsonify
from flask_cors import CORS
from pinecone_client import get_pinecone_index
from cohere_client import generate_embedding

# Initialize Flask app
app = Flask(__name__)

CORS(app)

# Initialize Pinecone index
index = get_pinecone_index()

@app.route('/query', methods=['POST'])
def query():
    data = request.json
    query_text = data.get('query', '')

    if not query_text:
        return jsonify({'error': 'Query text is required'}), 400

    # Generate embedding for the query text using Cohere
    query_embedding = generate_embedding(query_text)

    # Query Pinecone index
    results = index.query(
        vector=query_embedding,
        top_k=3,
        include_metadata=True
    )

    # Format response
    response_data = []
    for match in results['matches']:
        response_data.append({
            'score': match['score'],
            'instruction': match['metadata']['instruction'],
            'response': match['metadata']['response']
        })

    return jsonify({'results': response_data})

if __name__ == '__main__':
    app.run(debug=True)
