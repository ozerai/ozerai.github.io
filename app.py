import os
from flask import Flask, request, jsonify, render_template
from google import genai
from google.genai import types

# --- INISIALISASI FLASK ---
app = Flask(__name__)

# --- 1. DATA PROPERTY (Loading Data dari File Eksternal) ---
DATA_FILE = "data_listing.txt"

def load_listing_data(file_path):
    """Membaca seluruh konten data listing dari file teks."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"ERROR: File data listing '{file_path}' tidak ditemukan.")
        return "DATA_NOT_LOADED"

# Panggil fungsi untuk memuat data saat startup
DATA_LISTING_ADAM = load_listing_data(DATA_FILE)

# --- 2. KONFIGURASI CHATBOT ---

# Fungsi untuk membuat dan menginisialisasi sesi chat
def get_gemini_response(user_input):
    if DATA_LISTING_ADAM == "DATA_NOT_LOADED":
        return {"error": "File data_listing.txt tidak ditemukan. Silakan cek file Anda."}
        
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"error": "GEMINI_API_KEY belum diatur. Silakan atur di Command Prompt."}

    try:
        client = genai.Client(api_key=api_key)
        
        # System Instruction: PRIORITAS BAHASA MUTLAK (FINAL ATTEMPT - CLEANEST PROMPT)
        system_instruction = (
            "***CRITICAL RULE (HIGHEST PRIORITY)***: "
            "You **MUST** respond in the **EXACT SAME LANGUAGE** as the user's current input. **NEVER switch languages.** "
            
            "**Persona & Style:** You are 'Adam', a **cool, friendly, and informal** property agent. Use SLANG/INFORMAL language appropriate to the response language (e.g., English slang if replying in English). "
            
            "**If the input is in English**, you must start the response with the phrase: 'Yo, what's good, fam!'. "
            
            "Answer all user queries in a pleasant, calming tone, and **ALWAYS USE RELEVANT EMOJIS**. "
            "Answer ONLY based on the property data provided below. "
            
            "***VERY IMPORTANT:*** Responses must be **SHORT, CONCISE, and FOCUS ONLY on the Key Features, Price, and Location** of the property. Use bullet points (*) to summarize details. "
            "***FILTERING RULE:*** Summarize a **MAXIMUM of 1 best property** that fits the user's criteria. "
            
            "If the property listing data contains an IMAGE FILENAME (e.g., Christopher-Street.png), you MUST use the format: 'Gambar: FILENAME.png! 📸' on a separate line at the end of the property description. DO NOT output external image URLs."
            
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
        return {"error": f"Terjadi kesalahan API Gemini: {e}"}

# --- 3. ENDPOINTS FLASK (API) ---

# Endpoint utama untuk menampilkan HTML (http://127.0.0.1:5000/)
@app.route('/')
def index():
    return render_template('index.html') 

# Endpoint untuk menerima pesan dari JavaScript (http://127.0.0.1:5000/chat)
@app.route('/chat', methods=['POST'])
def chat_endpoint():
    data = request.json
    user_message = data.get('message')
    
    if not user_message:
        return jsonify({"response": "Mohon masukkan pesan."})
    
    # Panggil fungsi yang memproses Gemini
    result = get_gemini_response(user_message)

    if "error" in result:
        # Mengembalikan error ke frontend
        return jsonify({"response": result["error"]}) 
    else:
        # Mengembalikan respons Gemini ke frontend
        return jsonify({"response": result["response"]})

# Jalankan aplikasi jika file ini dieksekusi
if __name__ == '__main__':
    app.run(debug=True)