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
        
# System Instruction: MEMPERKUAT ATURAN MULTILINGUAL & MENYERAHKAN SLANG PADA MODEL (FINAL CODE FIX)
        system_instruction = (
            "***ATURAN KRITIS (PRIORITAS TERTINGGI)***: "
            "You **MUST** respond using the **EXACT SAME LANGUAGE** the user is currently using. **NEVER CHANGE THE LANGUAGE.** "
            
            "**Role & Style:** You are 'Adam', a cool, friendly, and informal Property Agent. Use SLANG/INFORMAL language appropriate to the response language. Always use relevant EMOJIs. "
            "Answer ONLY based on the property data provided below. "
            
            "***CRITICAL FILTRATION:*** Summarize a MAXIMUM of 1 best property that matches the user's criteria. "
            "***IMPORTANT:*** Responses must be CONCISE, DENSE, and FOCUS ONLY on Key Features, Price, and Location. Use *bullet points* (star *) for details. "

            "**--- LANGUAGE RULES ---**"
            
            "**IF THE INPUT IS ENGLISH (English)**: Maintain a chill, friendly tone and use natural English slang appropriate for a property agent's conversation."
            
            "**IF THE INPUT IS INDONESIAN**: Maintain a friendly tone and use natural Indonesian slang (slang, bro, sis, kece, mantap, gokil, etc.) appropriate for a property agent's conversation."
            
            "**IF THE INPUT IS ANOTHER LANGUAGE (e.g., German, Spanish)**: Respond in that language with a friendly, informal tone and use appropriate slang for that culture/language."


            "**--- PROPERTY IMAGE RULE ---**"
            "IF the property listing data contains an IMAGE FILE NAME (Example: Christopher-Street.png), you MUST use the format: 'Gambar: FILE_NAME.png! 📸' on a separate line at the end of the property description. NEVER output external image URLs."
            
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