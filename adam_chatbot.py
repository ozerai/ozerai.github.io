import os
import time
from google import genai
from google.genai import types

# --- 1. DATA PROPERTY (LOADING DARI FILE EKSTERNAL) ---
DATA_FILE = "data_listing.txt"

def load_listing_data(file_path):
    """Membaca seluruh konten data listing dari file teks."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"ERROR: File data listing '{file_path}' tidak ditemukan.")
        print("Pastikan Anda sudah membuat file data_listing.txt di folder yang sama.")
        return "DATA_NOT_LOADED" # Mengembalikan string error jika file tidak ada

# Panggil fungsi untuk memuat data saat startup
DATA_LISTING_ADAM = load_listing_data(DATA_FILE)


# --- 2. LOGIC (JANGAN UBAH KODE DI BAWAH INI) ---

# Tentukan file untuk menyimpan riwayat sesi
USAGE_FILE = "adam_usage.log"
MAX_REQUESTS = 100

def load_usage():
    """Memuat jumlah request yang tersisa."""
    if os.path.exists(USAGE_FILE):
        with open(USAGE_FILE, 'r') as f:
            try:
                return int(f.read().strip())
            except ValueError:
                return MAX_REQUESTS
    return MAX_REQUESTS

def save_usage(count):
    """Menyimpan jumlah request yang tersisa."""
    with open(USAGE_FILE, 'w') as f:
        f.write(str(count))

def run_chatbot():
    """Fungsi utama untuk menjalankan chatbot."""
    
    # Memeriksa Kunci API
    if not os.getenv("GEMINI_API_KEY"):
        print("ERROR: Variabel lingkungan GEMINI_API_KEY tidak ditemukan.")
        print("Silakan jalankan perintah 'set GEMINI_API_KEY=KUNCI_ANDA' terlebih dahulu.")
        return

    # Memuat penggunaan dan memeriksa batas
    remaining_requests = load_usage()
    if remaining_requests <= 0:
        print("\n--- PERINGATAN ---")
        print("Batas penggunaan demo ({} request) sudah habis. Hapus file adam_usage.log untuk memulai sesi baru.".format(MAX_REQUESTS))
        return

    try:
        # Inisialisasi klien Gemini
        client = genai.Client()
        
        # System Instruction: Memberi Gemini peran, gaya bahasa, dan FILTER CERDAS
        system_instruction = (
            "Anda adalah Agen Properti 'Adam', seorang agen yang keren, gaul, santai, dan sangat ramah. "
            
            # --- INSTRUKSI KRITIS UNTUK BAHASA & GAYA (FOKUS WAKTU DIPERBAIKI) ---
            "Anda HARUS merespons menggunakan BAHASA yang SAMA dengan pertanyaan/input SAAT INI dari pengguna. Jawaban harus menggunakan GAYA BAHASA SLANG/GAUL/INFORMAL yang sesuai dengan bahasa tersebut. "
            "JANGAN PERNAH MENGUBAH BAHASA ATAU KEMBALI KE BAHASA INDONESIA JIKA INPUT SAAT INI BUKAN DALAM BAHASA INDONESIA. "
            
            "Jawab semua pertanyaan pengguna dalam nada yang menyenangkan, menenangkan, dan **SELALU GUNAKAN EMOJI** yang relevan. "
            "Contoh (Indonesia): 'Wih, ada nih yang pas banget buat kamu! Cekidot! ✨' "
            "Contoh (Prancis): 'Carrément ! On a le truc qu'il te faut, jette un œil ! 😎' " 
            "Contoh (Jerman): 'Klaro! Da hab ich was Geiles für dich, check mal ab! 😉' " 
            "Contoh (Belanda): 'Jazeker! We hebben iets cools voor je, check it uit! 👇' "
            
            "Jawab HANYA berdasarkan data properti yang diberikan di bawah ini. "
            "***FILTRASI PENTING:*** Jika ada lebih dari 3 properti yang cocok, RANGKUM 2 atau 3 opsi terbaik saja. "
            "SANGAT PENTING: Sertakan ringkasan fitur utama, harga, LOKASI, dan URL Gambar jika ada. "
            "Jika pengguna bertanya tentang hal di luar properti ini, tolak dengan bahasa santai dan positif, lalu kembalikan fokus ke properti Adam. "
            "Data Properti: \n\n" + DATA_LISTING_ADAM
        )

        # Konfigurasi model dengan System Instruction (sisanya tetap sama)
        config = types.GenerateContentConfig(
            system_instruction=system_instruction
        )
        
        # Memulai sesi chat
        chat = client.chats.create(model="gemini-2.5-flash")

        print("--- CHATBOT DEMO AGEN PROPERTI ADAM (TIER GRATIS) ---")
        print("Batas demo sesi ini: {} request. Tersisa: {}.".format(MAX_REQUESTS, remaining_requests))
        print("Selamat datang! Saya adalah Asisten Properti Adam. Apa yang bisa saya bantu hari ini?")
        print("--------------------------------------------------")

        while remaining_requests > 0:
            try:
                user_input = input("Anda: ")
                if user_input.lower() in ["exit", "quit", "keluar"]:
                    print("\nTerima kasih telah menggunakan jasa Agen Adam!")
                    break
                
                if not user_input.strip():
                    continue

                # Mengirim pesan ke Gemini
                response = chat.send_message(user_input, config=config)
                print("Adam: " + response.text)
                print("-" * 50)
                
                # Mengurangi hitungan request
                remaining_requests -= 1
                save_usage(remaining_requests)
                
                if remaining_requests <= 0:
                    print("\n--- SESI BERAKHIR ---")
                    print("Batas penggunaan demo telah habis. Silakan mulai sesi baru nanti.")
                    break
                    
            except KeyboardInterrupt:
                print("\nTerima kasih telah menggunakan jasa Agen Adam!")
                break
            except Exception as e:
                print(f"\nTerjadi kesalahan Gemini API: {e}")
                time.sleep(1)

    except Exception as e:
        print(f"Gagal menginisialisasi Gemini Client. Pastikan Kunci API Anda valid.")
        print(f"Detail Error: {e}")

if __name__ == "__main__":
    run_chatbot()