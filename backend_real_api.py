import os
import json
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# 1. SETUP
load_dotenv()
app = Flask(__name__)
CORS(app)

API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=API_KEY)

# Use the 'gemini-flash-latest' model as you have currently configured
model = genai.GenerativeModel('gemini-flash-latest')

def clean_ai_response(text):
    """Ensures we only send pure JSON to the app."""
    text = text.replace("```json", "").replace("```", "").strip()
    return text

# --- HOME ROUTE (To kill the 404 once and for all) ---
@app.route('/')
def home():
    return "Manna AI Server is Online!"

# --- ROUTE 1: SHOPPING LIST (Your Energetic Nutritionist) ---
@app.route('/api/shop', methods=['POST'])
def generate_shop():
    try:
        data = request.json
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
        response = model.generate_content(prompt)
        return jsonify(json.loads(clean_ai_response(response.text)))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- ROUTE 2: RECIPE GENERATOR (Detailed Zero-Waste Logic) ---
@app.route('/api/recipes', methods=['POST'])
def generate_recipes():
    try:
        data = request.json
        inventory = data.get('inventory', [])
        profile = data.get('userProfile', {})

        prompt = f"""
        Role: Manna AI Personal Chef. 
        Objective: Kitchen on Autopilot.
        User Profile: {json.dumps(profile)}.
        Current Inventory: {json.dumps(inventory)}.

        STRICT DIETARY RULE: 
        The user follows a {profile.get('diet')} diet. 
        - If Diet is Pescetarian: NO chicken, beef, or pork. Only fish, seafood, and plants.
        - If Diet is Vegan: NO animal products at all.
        - If Diet is Vegetarian: NO meat or fish.

        TASK: 
        Generate 3 versatile recipes based on the user's specific diet and goal. 
        1. Recipe 1 MUST feature the inventory item with the lowest 'daysLeft' to prevent waste.
        2. Ensure the meals fit their {profile.get('vibe', 'balanced')} cooking vibe.
        3. Prioritize high-protein options if the goal is muscle building.

        Return ONLY a JSON array of recipe objects. No conversational text.
        """
        
        response = model.generate_content(prompt)
        return jsonify(json.loads(clean_ai_response(response.text)))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
