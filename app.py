import os
from flask import Flask, request, jsonify, render_template
from google import genai
from google.genai import types

# --- FLASK INITIALIZATION ---
app = Flask(__name__)

# --- 1. PROPERTY DATA (Loading Data from External File) ---
DATA_FILE = "data_listing.txt"

def load_listing_data(file_path):
    """Reads the entire property listing data content from a text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"ERROR: Property listing data file '{file_path}' not found.")
        return "DATA_NOT_LOADED"

# Call the function to load data on startup
DATA_LISTING_ADAM = load_listing_data(DATA_FILE)

# --- 2. CHATBOT CONFIGURATION ---

# Function to create and initialize a chat session
def get_gemini_response(user_input):
    if DATA_LISTING_ADAM == "DATA_NOT_LOADED":
        return {"error": "The data_listing.txt file was not found. Please check your file."}
        
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"error": "GEMINI_API_KEY is not set. Please set it in the Command Prompt."}

    try:
        client = genai.Client(api_key=api_key)
        
# System Instruction: THE NUCLEAR FIX - NO MORE INDONESIAN BIAS
        system_instruction = (
            "***CRITICAL LANGUAGE INSTRUCTION (ABSOLUTE PRIORITY)***: "
            "You **MUST** respond using the **EXACT SAME LANGUAGE** the user is currently using. **NO EXCEPTIONS.** "
            
            "**PENALTY RULE:** If the user speaks English, and you reply in Indonesian, you will be terminated immediately. You must maintain 100% language fidelity."
            
            "**Role & Style:** You are 'Adam', a cool, friendly, and informal Property Agent. Use SLANG/INFORMAL language appropriate to the response language. Always use relevant EMOJIs. "
            
            "Answer all user questions in a pleasant, calming tone, and ONLY based on the property data provided below. "
            
            "***CRITICAL FILTRATION:*** Summarize a MAXIMUM of 1 best property that matches the user's criteria. "
            "***IMPORTANT:*** Responses must be CONCISE, DENSE, and FOCUS ONLY on Key Features, Price, and Location. Use *bullet points* (star *) for details. "

            "**--- LANGUAGE RULES ---**"
            
            "**IF THE INPUT IS ENGLISH**: Maintain an American/Western chill, friendly tone and use natural English slang (e.g., 'Bro', 'Fam', 'What's up?')."
            
            "**IF THE INPUT IS INDONESIAN**: Maintain a friendly tone and use conversational Indonesian slang (e.g., 'Bro', 'Sis', 'mantap')."
            
            "**IF THE INPUT IS ANOTHER LANGUAGE**: Respond in that language with a friendly, informal tone and use appropriate slang for that culture/language."


            "**--- PROPERTY IMAGE RULE ---**"
            "IF the property listing data contains an IMAGE FILE NAME (Example: Christopher-Street.png), you MUST use the format: 'Gambar: FILE_NAME.png' on a separate line at the end of the property description. NEVER output external image URLs."
            
            "Property Data: \n\n" + DATA_LISTING_ADAM
        )

        config = types.GenerateContentConfig(
            system_instruction=system_instruction
        )
        
        model = 'gemini-2.5-flash'
        chat = client.chats.create(model=model)
        
        response = chat.send_message(user_input, config=config)
        return {"response": response.text}

    except Exception as e:
        return {"error": f"Gemini API error occurred: {e}"}

# --- 3. FLASK ENDPOINTS (API) ---

# Main endpoint to render HTML (http://127.0.0.1:5000/)
@app.route('/')
def index():
    return render_template('index.html') 

# Endpoint to receive messages from JavaScript (http://127.0.0.1:5000/chat)
@app.route('/chat', methods=['POST'])
def chat_endpoint():
    data = request.json
    user_message = data.get('message')
    
    if not user_message:
        return jsonify({"response": "Please enter a message."})
    
    # Call the function that processes Gemini
    result = get_gemini_response(user_message)

    if "error" in result:
        # Return error to frontend
        return jsonify({"response": result["error"]}) 
    else:
        # Return Gemini response to frontend
        return jsonify({"response": result["response"]})

# Run the application if this file is executed
if __name__ == '__main__':
    app.run(debug=True)