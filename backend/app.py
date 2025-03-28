from flask import Flask, request, jsonify
from flask_cors import CORS
from pinecone_client import get_pinecone_index
from cohere_client import generate_embedding, generate_final_answer, is_query_relevant
import random

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize Pinecone index
index = get_pinecone_index()

# Global variable to store chat history (can also be session-based)
chat_history = []

# Define intents with patterns and responses
intents = [
    {
        "tag": "greeting",
        "patterns": ["hi", "hello", "hey", "good morning", "good evening"],
        "responses": [
            "Hello! How can I assist you today?",
            "Hi there! What do you need help with?",
            "Greetings! How may I help you?"
        ]
    },
    {
        "tag": "goodbye",
        "patterns": ["bye", "goodbye", "see you", "exit"],
        "responses": [
            "Goodbye! Take care.",
            "See you later! Stay safe.",
            "Thanks for using the chatbot. Have a great day!"
        ]
    },
    {
        "tag": "file_FIR",
        "patterns": ["file FIR", "register FIR", "complaint", "report crime"],
        "responses": [
            "To file an FIR, visit your nearest police station with all relevant details about the incident.",
            "You can file an FIR by providing a written complaint at the police station in your jurisdiction."
        ]
    },
    {
        "tag": "emergency_contacts",
        "patterns": ["emergency number", "helpline", "emergency contact", "emergency", "help"],
        "responses": [
        (
            "Here are some important emergency numbers in India:\n"
            "- Police: 100\n"
            "- Fire: 101\n"
            "- Ambulance: 102\n"
            "- Women Helpline: 1091\n"
            "- Integrated Emergency Helpline (PAN-India): 112\n\n"
            "Please call the relevant service immediately if you are in danger."
        )
    ]
    }
]

# Function to classify intent based on user query
def classify_intent(query):
    query = query.lower()
    for intent in intents:
        for pattern in intent["patterns"]:
            if pattern.lower() in query:
                return intent["tag"]
    return None

@app.route('/query', methods=['POST'])
def query():
    try:
        # Parse incoming JSON request
        data = request.json
        query_text = data.get('query', '').strip()

        if not query_text:
            return jsonify({'answer': '⚠️ Please enter a valid query.'}), 400

        emergency_numbers = {
            "100": "📞 **Police** - Dialing **100**. Click <a href='tel:100'>here</a> to call.",
            "police": "📞 **Police** - Dialing **100**. Click <a href='tel:100'>here</a> to call.",
            "101": "🔥 **Fire Department** - Dialing **101**. Click <a href='tel:101'>here</a> to call.",
            "fire": "🔥 **Fire Department** - Dialing **101**. Click <a href='tel:101'>here</a> to call.",
            "102": "🚑 **Ambulance** - Dialing **102**. Click <a href='tel:102'>here</a> to call.",
            "ambulance": "🚑 **Ambulance** - Dialing **102**. Click <a href='tel:102'>here</a> to call.",
            "1091": "👩‍🦰 **Women Helpline** - Dialing **1091**. Click <a href='tel:1091'>here</a> to call.",
            "women helpline": "👩‍🦰 **Women Helpline** - Dialing **1091**. Click <a href='tel:1091'>here</a> to call.",
            "112": "🚨 **Integrated Emergency Helpline** - Dialing **112**. Click <a href='tel:112'>here</a> to call.",
            "emergency": "🚨 **Integrated Emergency Helpline** - Dialing **112**. Click <a href='tel:112'>here</a> to call."
        }

        # Check if query matches any emergency keyword
        if query_text in emergency_numbers:
            return jsonify({'answer': emergency_numbers[query_text]})

        # Classify intent
        intent = classify_intent(query_text)

        if intent:
            # Handle predefined intents
            for intent_data in intents:
                if intent_data["tag"] == intent:
                    response = random.choice(intent_data["responses"])
                    return jsonify({'answer': response})

        # Check if the query is relevant
        if not is_query_relevant(query_text):
            return jsonify({
                'answer': "I'm sorry, but your query does not seem relevant to legal matters or police procedures. Please ask about FIR filing, rights, or related topics."
            })

        # Generate embedding for the query text using Cohere
        query_embedding = generate_embedding(query_text)

        # Query Pinecone index for top 3 results
        results = index.query(
            vector=query_embedding,
            top_k=3,
            include_metadata=True
        )

        # Extract context from top 3 matches
        context = ""
        for match in results['matches']:
            context += f"Instruction: {match['metadata']['instruction']}\n"
            context += f"Response: {match['metadata']['response']}\n\n"

        # Generate final answer using Cohere's free-tier text generation model with chat history
        final_answer = generate_final_answer(query_text, chat_history)

         # Update chat history with user query and bot response
        chat_history.append({
            "user": query_text,
            "bot": final_answer
        })
        
        print(f"Query: {query_text}, Final Answer: {final_answer}")

        return jsonify({'answer': final_answer.replace("\n", "<br>")})  

    except Exception as e:
        # Log error for debugging purposes
        print(f"Error processing request: {e}")
        return jsonify({'answer': '🤖 Oops! Something went wrong on our end. Please try again later.'}), 500

# Welcome route (optional)
@app.route('/welcome', methods=['GET'])
def welcome():
    return jsonify({
        'message': (
            "Welcome to Legal AI Assistant! I'm here to provide professional legal guidance and answer your questions "
            "related to FIR filing, police procedures, and your rights under Indian law."
            "\n💡 Examples of questions you can ask:"
            "\n- How do I file an FIR?"
            "\n- What are my rights if arrested?"
            "\n- What documents are needed to file a complaint?"
        )
    })

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'answer': '🤖 Oops! Something went wrong on our end. Please try again later.'}), 500

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'answer': '⚠️ The requested resource was not found.'}), 404


if __name__ == '__main__':
    app.run(debug=True)
