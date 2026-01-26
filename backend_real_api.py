import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

app = Flask(__name__)
CORS(app)

# 2. Setup AI (With Safety Check)
if not API_KEY:
    print("❌ ERROR: GOOGLE_API_KEY not found.")
else:
    genai.configure(api_key=API_KEY)

# 3. GLOBAL MODEL CONFIG (The Fix)
# We use the exact name from your screenshot: 'gemini-flash-latest'
generation_config = {
  "temperature": 0.7,
  "top_p": 1,
  "top_k": 1,
  "max_output_tokens": 2048,
}

# THE CORRECT COMBINED VERSION:
model = genai.GenerativeModel('gemini-flash-latest', generation_config=generation_config)


def clean_ai_response(text):
    """Cleans up the AI's response to ensure valid JSON."""
    text = text.replace("```json", "").replace("```", "").strip()
    return text

# --- ROUTE 1: SHOPPING LIST (With Emojis) ---
@app.route('/api/shop', methods=['POST'])
def generate_shop():
    data = request.json
    print(f"🛒 Generating List for: {data}")

    # Prompt explicitly asks for Emojis
    prompt = f"""
    Act as a friendly, energetic nutritionist.
    Create a shopping list for: {data.get('goal', 'Healthy Living')}.
    Diet: {data.get('diet', 'Any')}.
    
    STRICT JSON OUTPUT ONLY. No talking.
    Return an ARRAY of objects. Each object must have:
    - name (string)
    - amount (string)
    - emoji (string: a relevant emoji like 🥦 or 🍗)
    - why (string: 1 short, fun sentence)

    Example:
    [
        {{"name": "Avocados", "amount": "2 count", "emoji": "🥑", "why": "Healthy fats for brain power!"}}
    ]
    """

    try:
        response = model.generate_content(prompt)
        clean_json = clean_ai_response(response.text)
        return jsonify(json.loads(clean_json))
    except Exception as e:
        print(f"❌ AI Error: {e}")
        # FALLBACK: If AI trips, return this safe list so the app NEVER crashes
        return jsonify([
            {"name": "Oats", "amount": "1 bag", "emoji": "🥣", "why": "AI is napping, but oats are forever."},
            {"name": "Berries", "amount": "1 pack", "emoji": "🍓", "why": "Antioxidants for the win."}
        ])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)