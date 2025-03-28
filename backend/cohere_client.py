import cohere
import os

def generate_embedding(text):
    COHERE_API_KEY = os.getenv("COHERE_API_KEY")
    
    # Initialize Cohere client
    co = cohere.Client(COHERE_API_KEY)

    # Generate embedding for the input text using a free-tier model
    response = co.embed(texts=[text], model="embed-english-light-v2.0", input_type="search_query")
    
    return response.embeddings[0]

def generate_final_answer(query, chat_history):
    COHERE_API_KEY = os.getenv("COHERE_API_KEY")
    
    # Initialize Cohere client
    co = cohere.Client(COHERE_API_KEY)

    # Combine chat history into a single string
    context = "\n".join([f"User: {entry['user']}\nBot: {entry['bot']}" for entry in chat_history])

    # Add the current query to the prompt
    prompt = f"""You are a legal expert and an Indian cop. You abide by the Indian constitution. Based on the following conversation history, answer the question in a short answer. Give the answer in the form of points:
Conversation History:
{context}

User's Question:
{query}

Answer:"""

    # Generate final answer using Cohere's free-tier text generation model
    response = co.generate(
        model="command",  # Updated to use v2 model
        prompt=prompt,
        max_tokens=500,
        temperature=0.3,
        # prompt_truncation="AUTO",
        stop_sequences=[]
    )
    
    return response.generations[0].text.strip()

def is_query_relevant(query):
    """
    Checks if the query is relevant to the chatbot's purpose.
    """
    # Define a list of relevant topics or keywords
    relevant_keywords = [
    # Legal & Police Keywords
    "FIR", "police", "rights", "arrest", "law", "legal", "complaint", "procedure", 
    "Indian law", "constitution", "punishment", "crime", "investigation", "punishments", 
    "report", "file", "register", "lodge", "submit", "online complaint", "written complaint", 
    "jurisdiction", "acknowledgment", "receipt", "complaint number", "case number", 
    "evidence", "witness", "statement", "signature", "process", "inquiry", "interrogation", 
    "detention", "custody", "bail", "remand", "charge sheet", "court", "hearing", 
    "trial", "timeline", "duration", "steps", "section", "act", "IPC", "CrPC", 
    "provision", "penalty", "fine", "imprisonment", "offense", "criminal", "civil", 
    "duties", "victim", "accused", "suspect", "defendant", "station", "thana", "address", 
    "location", "nearest", "area", "district", "city", "phone", "timing", "hours", "officer", 
    "SHO", "inspector", "constable", "personnel", "document", "ID", "identification", 
    "proof", "Aadhaar", "PAN", "passport", "license", "certificate", "photo", "copy", 
    "original", "attach", "upload", "theft", "robbery", "burglary", "assault", "attack", 
    "murder", "rape", "harassment", "fraud", "cheating", "cybercrime", "hacking", 
    "domestic violence", "abuse", "missing", "kidnapping", "damage", "property", 
    "vehicle", "status", "update", "progress", "follow-up", "track", "check", "verify", 
    "confirmation", "pending", "completed", "closed", "resolved", "action", "protection", 
    "safety", "security", "privacy", "confidential", "anonymous", "identity", 
    "witness protection", "legal aid", "lawyer", "advocate", "counsel", "advice", 
    "verification", "background check", "NOC", "clearance", "permission", "protest", 
    "gathering", "event", "procession", "rally", "demonstration", "bns", 

    # Emergency & Helpline Keywords
    "emergency", "helpline", "contact", "number", "dial", "call", "100", "112", 
    "ambulance", "fire", "accident", "crisis", "urgent", "immediate", "assistance", 
    "help", "rescue", "support", "danger", "threat",

    # Indian Constitution & Governance Keywords
    "constitution", "fundamental rights", "directive principles", "democracy", 
    "republic", "sovereignty", "secularism", "socialist", "justice", "equality", 
    "liberty", "fraternity", "citizenship", "preamble", "judiciary", "executive", 
    "legislature", "parliament", "president", "prime minister", "governor", "chief minister", 
    "council of ministers", "lok sabha", "rajya sabha", "state assembly", "state council", 
    "federalism", "union government", "state government", "municipality", "panchayat", 
    "fundamental duties", "directive principles of state policy", "reservation", "SC/ST", 
    "OBC", "minorities", "freedom of speech", "freedom of expression", "freedom of religion", 
    "right to education", "right to information", "right to equality", "right to life", 
    "writ", "habeas corpus", "mandamus", "quo warranto", "certiorari", "prohibition", 
    "elections", "voting rights", "representation", "universal suffrage", "caste system", 
    "untouchability", "social justice", "economic justice", "political justice", 
    "national emergency", "president’s rule", "governor’s rule", "martial law", "habeas corpus", 
    "fund allocation", "GST", "financial commission", "planning commission", "NITI Aayog", 
    "supreme court", "high court", "district court", "tribunals", "NHRC", "NCW", "NCSC", 
    "NCPCR", "Lokpal", "Lokayukta", "RTI", "RTE", "consumer protection", "environmental laws", 
    "wildlife protection", "forest conservation", "climate change", "pollution control", 
    "employment rights", "labor laws", "minimum wage", "trade unions", "industrial disputes", 
    "child labor", "bonded labor", "human trafficking", "women’s rights", "dowry prohibition", 
    "marriage laws", "divorce laws", "inheritance laws", "property rights", "intellectual property", "sexual harassment"
    
    # Indian Penal Code (IPC) & Criminal Procedure Code (CrPC) Keywords
    "IPC", "CrPC", "sections", "article", "penal code", "penalty", "punishment", "bailable", 
    "non-bailable", "compoundable", "non-compoundable", "cognizable offense", "non-cognizable offense", 
    "warrant", "summons", "arrest warrant", "search warrant", "police custody", "judicial custody", 
    "remand", "bail hearing", "plea", "public prosecutor", "defense lawyer", "witness statement", 
    "cross-examination", "evidence act", "forensic", "DNA test", "fingerprint analysis", 
    "lie detector test", "narco analysis", "crime scene", "FSL report", "charge sheet", 
    "trial procedure", "appellate court", "special court", "fast track court", "anti-corruption laws", 
    "bribery", "money laundering", "black money", "benami transactions", "cyber security", 
    "digital evidence", "online fraud", "phishing", "identity theft", "hacking laws"
]


    # Check if any keyword is present in the query
    for keyword in relevant_keywords:
        if keyword.lower() in query.lower():
            return True

    return False