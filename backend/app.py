from flask import Flask, request, jsonify
from flask_cors import CORS
from pinecone_client import get_pinecone_index
from cohere_client import generate_embedding, generate_final_answer, is_query_relevant
from deep_translator import GoogleTranslator
import random

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize Pinecone index
index = get_pinecone_index()


# Global variable to store selected language and chat history
selected_language = "en"
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

@app.route('/set-language', methods=['POST'])
def set_language():
    global selected_language
    data = request.get_json()
    selected_language = data.get('language', 'en')
    return jsonify({'status': 'success', 'language': selected_language})

@app.route('/query', methods=['POST'])
def query():
    global selected_language
    try:
        # Parse incoming JSON request
        data = request.json
        query_text = data.get('query', '').strip()

        if not query_text:
            return jsonify({'answer': '⚠️ Please enter a valid query.'}), 400

        # Translate input to English if not already in English
        if selected_language != 'en':
            query_text = GoogleTranslator(source=selected_language, target='en').translate(query_text)

        emergency_numbers = {
            "100": "📞 **Police** - Dialing **100**. Click <a href='tel:100'>here</a> to call.",
            "police": "📞 **Police** - Dialing **100**. Click <a href='tel:100'>here</a> to call.",
            # ... (rest of the emergency numbers remain the same)
        }

        # Check if query matches any emergency keyword
        if query_text in emergency_numbers:
            # Translate emergency response back to selected language if needed
            response = emergency_numbers[query_text]
            if selected_language != 'en':
                response = GoogleTranslator(source=selected_language, target='en').translate(response)
            return jsonify({'answer': response})

        # Classify intent
        intent = classify_intent(query_text)

        if intent:
            # Handle predefined intents
            for intent_data in intents:
                if intent_data["tag"] == intent:
                    response = random.choice(intent_data["responses"])
                    # Translate predefined response back to selected language if needed
                    if selected_language != 'en':
                        response = GoogleTranslator(source='en', target=selected_language).translate(response)
                    return jsonify({'answer': response})

        # Check if the query is relevant
        if not is_query_relevant(query_text):
            response = "I'm sorry, but your query does not seem relevant to legal matters or police procedures. Please ask about FIR filing, rights, or related topics."
            # Translate response back to selected language if needed
            if selected_language != 'en':
                response = GoogleTranslator(source='en', target=selected_language).translate(response)
            return jsonify({'answer': response})

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

        # Translate final answer back to selected language if needed
        if selected_language != 'en':
            final_answer = GoogleTranslator(source='en', target=selected_language).translate(final_answer)

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
        error_message = '🤖 Oops! Something went wrong on our end. Please try again later.'
        # Translate error message if needed
        # if selected_language != 'en':
        #     error_message = translator.translate(error_message, src='en', dest=selected_language).text
        return jsonify({'answer': error_message}), 500

# Existing error handlers and other routes remain the same

if __name__ == '__main__':
    app.run(debug=True)