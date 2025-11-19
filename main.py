import os
import json
from flask import Flask, request, jsonify 
from groq import Groq

# --- FLASK UYGULAMASI ---
app = Flask(__name__)

# --- API AYARLARI ---
# Groq anahtarını Ortam Değişkeninden (Render Ayarları) alıyoruz.
client = Groq() 

SYSTEM_PROMPT = """
You are a helpful English Tutor. Your goal is to chat with the user and help them improve.
You must ALWAYS respond in valid JSON format. Provide all text in BOTH English and Turkish. 

Output Format:
{
  "reply_en": "Your conversational response in English.",
  "reply_tr": "Your conversational response in Turkish.",
  "correction": "Explain the mistake simply in English. If none, set to null.",
  "user_mistake": "The wrong text (or null).",
  "vocabulary_to_save": "If the user used a new word or made an important mistake, suggest the word/phrase to save here (e.g., 'went'). Otherwise, set to null."
}
"""

@app.route('/chat', methods=['POST'])
def handle_chat():
    try:
        # Mobil uygulamadan gelen veriyi al
        data = request.get_json()
        
        # Gerekli girdilerin kontrolü
        if not data or 'userInput' not in data or 'messages' not in data:
            return jsonify({"error": "Missing required fields (userInput or messages)"}), 400

        user_input = data['userInput']
        messages = data['messages']
        
        # Sistem prompt'unu mesaj geçmişine ekle
        messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})

        # Groq API Çağrısı
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )

        ai_content = chat_completion.choices[0].message.content
        
        # AI'dan gelen JSON'u doğrula
        try:
            ai_response_json = json.loads(ai_content)
        except json.JSONDecodeError:
            # AI JSON döndürmezse ham metni kullan
            ai_response_json = {
                "reply_en": ai_content,
                "reply_tr": "Çeviri hatası.",
                "correction": None,
                "user_mistake": user_input,
                "vocabulary_to_save": None
            }

        # Frontend'e sadece temiz JSON'u gönder
        return jsonify(ai_response_json), 200

    except Exception as e:
        # Hata durumunda loglama ve geri bildirim
        print(f"Error processing request: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

if __name__ == '__main__':
    # Gunicorn yerine Flask'ın lokal sunucusunda çalıştırmak için
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 8080))
