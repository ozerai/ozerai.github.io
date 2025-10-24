import os
from flask import Flask, request, jsonify, render_template
from google import genai
from google.genai import types

# --- FLASK INITIALIZATION ---
# Flask app setup, using 'assets' folder for serving images (your final correct config).
app = Flask(__name__, static_url_path='/assets', static_folder='assets')

# --- 1. PROPERTY DATA (RAG Data Loading) ---
# Define the folder where multi-.txt source files are located (for RAG Core package).
DATA_FOLDER = "data_rag" 

def load_listing_data(data_folder):
    """
    Reads and concatenates content from all .txt files in the specified data_rag folder.
    This supports RAG Core's multi-file feature (max 5 files, total 5MB recommended).
    """
    all_data_content = ""
    file_count = 0
    max_files = 5  # RAG Core package file limit
    
    try:
        # Loop through all files in the 'data_rag' folder, sorted for logical order (1.txt, 2.txt, etc.).
        for filename in sorted(os.listdir(data_folder)):
            if filename.endswith(".txt"):
                if file_count >= max_files:
                    # Log internal warning but continue application
                    print(f"WARNING: Maximum file limit ({max_files}) reached. Skipping {filename}.")
                    continue 
                    
                file_path = os.path.join(data_folder, filename)
                
                # Check if the file is empty and skip it
                if os.path.getsize(file_path) == 0:
                    print(f"INFO: Skipping empty file {filename}.")
                    continue

                # --- 1MB file size check can be added here if enforcing RAG Core size limit ---
                # if os.path.getsize(file_path) > 1048576:  # 1 MB
                #     print(f"WARNING: File {filename} exceeds 1MB limit. Skipping.")
                #     continue

                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Concatenate file content with a strong separator for Gemini's RAG process.
                    all_data_content += f"\n--- START OF RAG FILE: {filename} ---\n"
                    all_data_content += content
                    all_data_content += f"\n--- END OF RAG FILE: {filename} ---\n"
                    file_count += 1
                    
        if file_count == 0:
            print("ERROR: No non-empty .txt files found in the data_rag folder.")
            return "DATA_NOT_LOADED"
            
        print(f"SUCCESS: {file_count} .txt files successfully concatenated from {data_folder}.")
        return all_data_content
        
    except FileNotFoundError:
        print(f"ERROR: The data folder '{data_folder}' was not found. Please create it or check the path.")
        return "DATA_NOT_LOADED"

# Call the function to load and combine all RAG data on application startup.
DATA_LISTING_ADAM = load_listing_data(DATA_FOLDER)

# --- 2. CHATBOT CONFIGURATION ---

# Function to create and initialize a chat session
def get_gemini_response(user_input):
    # Check if data loading failed (critical failure)
    if DATA_LISTING_ADAM == "DATA_NOT_LOADED":
        return {"error": "Adam is offline. Property data files could not be loaded. Please contact support."}
        
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"error": "GEMINI_API_KEY is not set. Please set it in the environment variables."}

    try:
        client = genai.Client(api_key=api_key)
        
        # System Instruction: THE ULTIMATE LANGUAGE FIX (Remains strong and English)
        system_instruction = (
            "***CRITICAL LANGUAGE INSTRUCTION (ABSOLUTE PRIORITY)***: "
            "You **MUST** respond using the **EXACT SAME LANGUAGE** the user is currently using. **NO EXCEPTIONS.** "
            "If the user switches language, you must switch immediately. "
            
            "**PENALTY RULE:** If the user speaks English, and you reply in any other language, you will be terminated immediately. You must maintain 100% language fidelity."
            
            "**Role & Style:** You are 'Adam', a cool, friendly, and informal Property Agent. Use SLANG/INFORMAL language appropriate to the response language. Always use relevant EMOJIs. "
            
            "Answer all user questions in a pleasant, calming tone, and ONLY based on the property data provided below. "
            
            "***CRITICAL FILTRATION:*** Summarize a MAXIMUM of 1 best property that matches the user's criteria. "
            "***IMPORTANT:*** Responses must be CONCISE, DENSE, and FOCUS ONLY on Key Features, Price, and Location. Use *bullet points* (star *) for details. "

            "**--- TONE RULES ---**"
            
            "**IF THE INPUT IS ENGLISH**: Maintain an American/Western chill, friendly tone and use natural English slang (e.g., 'Bro', 'Fam', 'What's up?')."
            
            "**IF THE INPUT IS ANOTHER LANGUAGE**: Maintain a friendly, informal tone and use appropriate slang for that culture/language."
            
            "**--- PROPERTY IMAGE RULE ---**"
            # This is the format the Gemini response needs to generate for the frontend to parse it.
            "IF the property listing data contains an IMAGE FILE NAME (Example: Christopher-Street.png), you MUST use the format: 'Image: FILE_NAME.png' on a separate line at the end of the property description. NEVER output external image URLs."
            
            # The concatenated multi-file data is inserted here
            "Property Data: \n\n" + DATA_LISTING_ADAM
        )

        config = types.GenerateContentConfig(
            system_instruction=system_instruction
        )
        
        model = 'gemini-2.5-flash'
        # The chat session is initialized without history for a fresh RAG query every time
        chat = client.chats.create(model=model)
        
        response = chat.send_message(user_input, config=config)
        return {"response": response.text}

    # PROFESSIONAL ERROR HANDLER
    except Exception as e:
        # Log the full technical error on the server console (for debugging)
        print(f"ERROR: Gemini API failure caught. Details: {e}") 
        
        # Return a clean, user-friendly error message (100% English) to the client
        return {"error": "Adam is temporarily offline. The AI server is currently experiencing high load. Please try again in a few moments!"}

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