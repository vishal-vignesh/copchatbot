from flask import Flask, request, jsonify
from flask_cors import CORS
from pinecone_client import get_pinecone_index
from cohere_client import generate_embedding, generate_final_answer, is_query_relevant
from deep_translator import GoogleTranslator
import random
import requests
from math import radians, sin, cos, sqrt, atan2
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
    },
    {
        "tag": "nearby_police_stations",
        "patterns": [
            "police station near me", 
            "nearby police stations", 
            "closest police station", 
            "find police stations", 
            "locate police station",
            "nearest police station",
            "where is the closest police station?",
            "show me nearby police stations",
            "how can I find a police station?",
            "police stations around me",
            "police stations in my area",
            "where is the nearest police station?",
            "find police station near my location",
            "nearby police post",
            "closest law enforcement office",
            "find cops nearby",
            "where is the closest cop station?",
            "police stations within my city",
            "show police stations near my location",
            "I need a police station now",
            "where can I report a crime?",
            "where do I go for police assistance?",
            "nearest police help center",
            "find law enforcement office nearby",
            "nearest emergency police station",
            "where is the police department?",
            "where can I find a police station?",
            "can you show me nearby police stations?",
            "is there a police station nearby?",
            "any police stations near me?",
            "how do I get to the nearest police station?",
            "help me find a police station",
            "need to go to a police station",
            "police staion near me",
            "police staton close to me",
            "polce station nearby",
            "near police station",
            "where find police station?",
            "close police station"
        ],
        "responses": [
            "To find nearby police stations, please click the 'Find Nearby Police Stations' button in the interface.",
            "Use the geolocation feature to locate the nearest police stations by clicking the designated button.",
            "The app can help you find police stations close to your current location. Please use the 'Find Nearby Police Stations' button."
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
    global selected_language, chat_history
    data = request.get_json()
    new_language = data.get('language', 'en')

    # Only reset chat history if the language has actually changed
    if new_language != selected_language:
        chat_history = []  # Clear chat history to remove mixed-language responses
    
    selected_language = new_language
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
                    # Special handling for nearby police stations intent
                    if intent == "nearby_police_stations":
                        response = (
                            "To find nearby police stations:\n"
                            "1. Click the 'Find Nearby Police Stations' button\n"
                            "2. Allow location access\n"
                            "3. The app will list nearby police stations with their names, addresses, and distances"
                        )
                    else:
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
     
def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    radius = 6371  # Radius of earth in kilometers

    return radius * c
@app.route('/nearby-police-stations', methods=['POST'])
def find_nearby_police_stations():
    try:
        # Get location from request
        data = request.json
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        # Google Places API endpoint
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        
        # Parameters for the API request
        params = {
            'location': f"{latitude},{longitude}",
            'radius': 10000,  # 5 km radius
            'type': 'police',
            'key': 'AIzaSyB8Nt1cjaCAco1td71T_T_cREkKg6v9ybc'
        }

        # Make request to Google Places API
        response = requests.get(url, params=params)
        results = response.json().get('results', [])

        # Process and filter stations
        nearby_stations = []
        for station in results:
            # Calculate distance
            station_lat = station['geometry']['location']['lat']
            station_lng = station['geometry']['location']['lng']
            distance = haversine_distance(latitude, longitude, station_lat, station_lng)

            # Add station details
            nearby_stations.append({
                'name': station.get('name', 'Police Station'),
                'vicinity': station.get('vicinity', 'Location not available'),
                'distance': distance
            })

        # Sort stations by distance
        nearby_stations.sort(key=lambda x: x['distance'])

        # Prepare formatted response for chat
        if nearby_stations:
            stations_text = "🚨 Nearby Police Stations:\n\n"
            for station in nearby_stations[:5]:
                stations_text += (
                    f"📍 *{station['name']}*\n"
                    f"Address: {station['vicinity']}\n"
                    f"Distance: {station['distance']:.2f} km\n\n"
                )
            
            return jsonify({'answer': stations_text})
        else:
            return jsonify({'answer': "No police stations found within 5 km."})

    except Exception as e:
        print(f"Error finding nearby police stations: {e}")
        return jsonify({
            'answer': 'Unable to find nearby police stations. Please try again.'
        }), 500

if __name__ == '__main__':
    app.run(debug=True)