import google.generativeai as genai
import requests
import json
import re
import time
import os
from dotenv import load_dotenv

load_dotenv()

def create_tag_from_collocation(text):
    """ 'pose a risk' -> 'vocab:pose_a_risk' çevirimi yapar """
    # Boşlukları alt çizgi yap, küçük harfe çevir
    clean_text = re.sub(r'\s+', '_', text.strip().lower())
    # Sadece harf, rakam ve alt çizgi kalsın (Güvenlik)
    clean_text = re.sub(r'[^a-z0-9_]', '', clean_text)
    return f"vocab:{clean_text}"


# --- AYARLAR ---
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("❌ HATA: API Key bulunamadı! .env dosyasını kontrol et.")

ANKI_URL = "http://localhost:8765"
DECK_NAME = "Default"       # Anki Deste adın (Emin ol!)
MODEL_NAME = "Boşluklu"     # Not Tipi adın
INPUT_FILE = "input.txt"    # Okunacak dosya adı

# Gemini Konfigürasyonu (Hızlı model)
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

def clean_json_response(text):
    """
    Gemini bazen JSON verisini Markdown blokları (```json ... ```) içine gömer.
    Bu fonksiyon o gereksiz süsleri temizler, saf JSON metni bırakır.
    """
    text = text.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()

def generate_card_content(target_collocation):
    """
    Gemini'ye bağlanır ve C1 seviyesinde, İPUÇLU (HINT) formatında veri ister.
    """
    print(f"🤖 Gemini İşliyor: '{target_collocation}'...")
    
    # PROMPT MÜHENDİSLİĞİ:
    # Modele kesin emirler veriyoruz. Formatı bozuk atarsa kod patlar.
    # Özellikle {{c1::kelime::ipucu}} formatını zorluyoruz.
    prompt = f"""
    You are an expert English tutor preparing Anki flashcards for a Data Science student aiming for C1 level.
    Target Collocation: "{target_collocation}"

    Create a JSON object with exactly these keys:
    1. "definition": A concise English definition (max 5-6 words).
    2. "sentence": A sophisticated C1-level sentence. 
       You MUST use Anki cloze deletion syntax WITH A HINT.
       Format: {{{{c1::target collocation::definition}}}}
       (Insert the definition from step 1 as the hint inside the cloze).
       Example: "The study {{{{c1::accounts for::explains the cause of}}}} the missing data." 
    3. "collocations": 3 other high-level collocations using the main word, separated by ' | '.

    Output ONLY valid JSON. No extra text.
    """
    
    try:
        response = model.generate_content(prompt)
        cleaned_json = clean_json_response(response.text)
        return json.loads(cleaned_json) # String'i Python Sözlüğüne (Dict) çevirir
    except Exception as e:
        print(f"❌ Gemini Hatası ({target_collocation}): {e}")
        return None

def add_note_to_anki(data, original_collocation):
    """
    Hazırlanan veriyi HTTP POST isteği ile AnkiConnect'e yollar.
    """

    vocab_tag = create_tag_from_collocation(original_collocation)

    note_payload = {
        "deckName": DECK_NAME,
        "modelName": MODEL_NAME,
        "fields": {
            "Metin": data["sentence"],          # Ön Yüz (Cümle + Boşluk)
            "Back Extra": f"<b>Tanım:</b> {data['definition']}", # Arka Yüz
            "Collocations": data["collocations"] # Ekstra Alan
        },
        "tags": ["Gemini_Batch", "C1_Vocab", vocab_tag] # Etiketliyoruz ki sonra bulması kolay olsun
    }

    try:
        response = requests.post(ANKI_URL, json={
            "action": "addNote",
            "version": 6,
            "params": {"note": note_payload}
        })
        result = response.json()
        
        if result.get("error") is None:
            print(f"✅ EKLENDİ: {data['sentence'][:50]}...") # Cümlenin başını yazdır
            return True
        else:
            print(f"⚠️ ANKI REDDETTİ: {result['error']}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ KRİTİK HATA: Anki Masaüstü uygulaması kapalı! Bağlanamıyorum.")
        return False


def check_if_exists(collocation):
    """
    Anki'ye sorar: Bu özel etikete (tag) sahip kart var mı?
    """
    tag_to_search = create_tag_from_collocation(collocation)
    # Sorgu değişti: 'tag:vocab:kelime_adi'
    query = f'deck:"{DECK_NAME}" tag:{tag_to_search}'
    
    try:
        response = requests.post(ANKI_URL, json={
            "action": "findNotes",
            "version": 6,
            "params": {"query": query}
        })
        result = response.json()
        if result.get("result"): 
            return True # VAR
        else:
            return False # YOK
    except:
        return False
    

def process_batch_file():
    """
    Ana Operasyon Merkezi: Dosyayı okur, döngüyü kurar, işi bitirir.
    """
    try:
        # encoding="utf-8" yoksa Türkçe karakterler bozuk çıkar.
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        print(f"\n📂 '{INPUT_FILE}' bulundu. Toplam {len(lines)} satır işlenecek.\n")
        
        success_count = 0
        
        for index, line in enumerate(lines):
            collocation = line.strip() # Satır sonundaki boşlukları ve \n siler
            
            if not collocation: # Boş satırsa atla
                continue


                # --- YENİ KONTROL ---
            print(f"🔍 Kontrol ediliyor: '{collocation}'...")
            if check_if_exists(collocation):
                print(f"⏭️  ATLANDI: '{collocation}' zaten mevcut.")
                continue # Bir sonraki kelimeye geç
            # --------------------
                
            # Eğer yoksa Gemini'ye git...
            content = generate_card_content(collocation)


            if content:
                # 2. Anki'ye Yolla
                if add_note_to_anki(content, collocation):
                    success_count += 1
            
            # Rate Limiting (Hız Sınırlama)
            # API'yi ve Anki'yi boğmamak için her işlemden sonra 1.5 saniye bekle.
            time.sleep(4)
            print("-" * 40)

        print(f"\n🏁 İŞLEM TAMAMLANDI: {success_count}/{len(lines)} kart başarıyla eklendi.")

    except FileNotFoundError:
        print(f"❌ HATA: '{INPUT_FILE}' dosyası bulunamadı! Lütfen proje klasörüne bu dosyayı oluştur.")

# --- BAŞLAT ---
if __name__ == "__main__":
    process_batch_file()