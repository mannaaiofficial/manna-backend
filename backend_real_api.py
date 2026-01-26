import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

# 2. Setup Flask & Gemini
app = Flask(__name__)
CORS(app)

if not API_KEY:
    print("❌ ERROR: GOOGLE_API_KEY not found in .env file.")
else:
    genai.configure(api_key=API_KEY)
    print("✅ AI Brain Connected.")

# --- HELPER: CLEAN JSON ---
def clean_ai_response(text):
    """Removes markdown code blocks if the AI adds them."""
    text = text.replace("```json", "").replace("```", "").strip()
    return text

# --- ROUTE 1: SMART SHOPPING LIST ---
@app.route('/api/shop', methods=['POST'])
def generate_shop():
    data = request.json
    print(f"🛒 Generating Shopping List for: {data}")

    # The Prompt that forces Rich Data
    prompt = f"""
    Act as a professional nutritionist and chef.
    Create a shopping list for a student who wants to cook {data.get('vibe', 'Simple')} meals.
    Their Goal: {data.get('goal', 'General Health')}.
    Their Diet: {data.get('diet', 'Anything')}.
    Shopping Duration: {data.get('days', 3)} days.

    STRICT OUTPUT FORMAT: Return ONLY a raw JSON array. Do not talk.
    Each item must have:
    - name (string)
    - amount (string)
    - nutrition (string: brief benefit, e.g. "High Protein")
    - substitute (string: a valid alternative)
    - why (string: 1 short sentence linking it to their goal "{data.get('goal')}")

    Example JSON Structure:
    [
        {{"name": "Salmon", "amount": "2 fillets", "nutrition": "Omega-3s", "substitute": "Trout or Tofu", "why": "Omega-3s support brain function for your studies."}}
    ]
    """

    try:
        model = genai.GenerativeModel('gemini-pro)
        response = model.generate_content(prompt)
        clean_json = clean_ai_response(response.text)
        return jsonify(json.loads(clean_json))
    except Exception as e:
        print(f"❌ AI Error: {e}")
        return jsonify({"error": str(e)}), 500

# --- ROUTE 2: SMART RECIPES ---
@app.route('/api/recipes', methods=['POST'])
def generate_recipes():
    data = request.json
    print(f"👨‍🍳 Generating Recipes for: {data.get('ingredients')}")

    prompt = f"""
    You are a zero-waste chef.
    The user has these ingredients: {', '.join(data.get('ingredients', []))}.
    Cooking Vibe: {data.get('vibe', 'Speed')}.

    Create 3 recipes that use these ingredients. Prioritize using items that expire soon.
    STRICT OUTPUT FORMAT: Return ONLY a raw JSON array.
    Each recipe must have:
    - id (string: unique number)
    - type (string: Breakfast, Lunch, or Dinner)
    - title (string)
    - description (string: enticing 1 liner)
    - calories (number: integer estimate)
    - macros (object: {{p: number, c: number, f: number}})
    - time (string: e.g. "15 mins")
    - difficulty (string: Easy/Medium/Hard)
    - ingredients (array of objects: {{name, amount}})
    - instructions (array of strings)
    - image (string: Use a generic unsplash URL for this food type)
    """

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        clean_json = clean_ai_response(response.text)
        return jsonify(json.loads(clean_json))
    except Exception as e:
        print(f"❌ AI Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)