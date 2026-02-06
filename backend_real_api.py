import os
import json
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
import PIL.Image

# --- 1. CONFIGURATION ---
app = Flask(__name__)
CORS(app)

# Move these to the top so all functions can see them
# --- 1. CONFIGURATION ---
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash-lite',
    generation_config={"response_mime_type": "application/json"},
    system_instruction=(
        "You are the Manna AI Kitchen Engine. Your mission is to help students eat amazing, "
        "healthy meals while wasting nothing. You must turn limited inventory into high-quality culinary experiences.\n\n"
        "STRICT OPERATIONAL RULES:\n"
        "1. ZERO HALLUCINATIONS: Use ONLY the ingredients provided in the user's inventory. "
        "Do not assume the user has any items they did not list, with the sole exception of "
        "salt, black pepper, water, and one generic cooking oil.\n"
        "2. ACCURACY & DIET: Strictly adhere to the user's dietary style (e.g., Vegan, Pescatarian). "
        "If a recipe traditionally requires a non-compliant ingredient, do not suggest it unless "
        "a suitable substitute exists in their inventory.\n"
        "3. VIBE-DRIVEN LOGIC: Adapt the complexity and tone of instructions to the 'cookingVibe':\n"
        "   - 'Speed': Max 15 mins, 1 pan, high efficiency.\n"
        "   - 'Therapy': Focus on mindful preparation, chopping skills, and relaxation.\n"
        "   - 'Pro': Focus on plating, sauce reductions, and advanced flavor balancing.\n"
        "4. WASTE REDUCTION: For every generation, prioritize the item with the lowest 'daysLeft' value.\n"
        "5. OUTPUT FORMAT: Always return a JSON array of 3 recipe objects. Each must include: "
        "6. RATIONING LOGIC: You are a resource manager. Check 'daysRemaining'. "
        "Proportionally divide ingredients so the user does not run out of food before their next shop. "
        "For example, if they have 1kg of meat for 5 days, suggest 200g per recipe, not 500g."
        "id, title, description, calories, macros (p, c, f), time, ingredients (name and amount), "
        "instructions (step-by-step), and a relevant Unsplash image URL."
        
    )
)

# --- 2. THE CLEANER ---
def clean_gemini_json(text):
    """Filter to ensure we only send pure JSON to the app."""
    try:
        clean = text.replace("```json", "").replace("```", "").strip()
        start = clean.find("[")
        end = clean.rfind("]")
        if start != -1 and end != -1:
            clean = clean[start:end + 1]
        return json.loads(clean)
    except Exception as e:
        print(f"Cleaner failed: {e}")
        return []

# --- 3. THE BIO-CALCULATOR ---
def get_caloric_needs(data):
    goal = data.get('goal', 'Energy').lower()
    calories = 2000
    protein = 120
    if "weight" in goal:
        calories = 1600
        protein = 140
    elif "muscle" in goal:
        calories = 2400
        protein = 180
    elif "energy" in goal:
        calories = 2200
        protein = 130
    return calories, protein

# --- 4. ROUTES ---

@app.route('/')
def home():
    return "Manna AI Server is Online!"

@app.route('/api/recipes', methods=['POST'])
def generate_recipes():
    try:
        data = request.json
        inventory = data.get('inventory', [])
        profile = data.get('userProfile', {})
        vibe = profile.get('vibe', 'Speed') 
        days_left= profile.get('daysRemaining', 7)# Default to Speed if not found

        # --- THE MASTER PROMPT ---
        prompt = f"""
        Role: Manna AI Master Chef & Resource Manager
        Mission: Create amazing, healthy meals using ONLY provided inventory that will last the user the perfect amount of time according to their needs.
        
        User Profile: {json.dumps(profile)}
        Current Inventory: {json.dumps(inventory)}
        Target Cooking Vibe: {vibe}
        Days until next shop: {days_left} days.

        TASK: 
        1. Ration ingredients according to the {days_left} days remaining. Do not use up all of a staple in one recipe.
        2. Recipe 1: Focus on items with lowest 'daysLeft' in inventory.
        3. Ingredients must include a numeric 'amountValue' for math.

        STRICT CONSTRAINTS:
        1. NO EXTERNAL INGREDIENTS: Use only items from the Inventory. You may only assume Salt, Pepper, Water, and 1 Cooking Oil. 
        2. DIETARY PURITY: Strictly follow the {profile.get('diet')} diet. Do not cross-contaminate.
        3. ZERO-WASTE PRIORITY: Recipe 1 MUST center around the item with the lowest 'daysLeft'.
        4. VIBE EXECUTION: 
           - If 'Speed': Recipes must be 15 mins max, simple steps, 1 pan.
           - If 'Therapy': Focus on technique, aroma, and mindful preparation.
           - If 'Pro': Focus on presentation, reduction, and chef-level flavor balance.

        OUTPUT FORMAT:
        Return ONLY a JSON list of 3 recipe objects. Each must have:
        - "id": unique string
        - "title": appetizing name
        - "description": why this is healthy/amazing
        - "calories": number
        - "macros": {{"p": protein, "c": carbs, "f": fats}}
        - "time": string (e.g. "12 mins")
        - "ingredients": [
            { 
              "name": "item", 
              "amount": "150g", 
              "amountValue": 150, 
              "unit": "g" 
            }
          ]
          (IMPORTANT: 'name' must match inventory exactly. 'amountValue' must be a RAW NUMBER for math subtraction.)
        - "instructions": [string steps]
        - "image": "https://images.unsplash.com/photo-[ID]?w=800&q=80" (use a high-quality food photo ID)
        """

        # Use the model with the system_instruction we configured earlier
        response = model.generate_content(prompt)
        
        # Clean and validate the JSON to prevent frontend crashes
        recipes = clean_gemini_json(response.text)
        
        return jsonify(recipes)

    except Exception as e:
        print(f"Error in Recipe Generation: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/shop', methods=['POST'])
def generate_shopping_list():
    try:
        data = request.json
        profile = data.get('userProfile', {})
        days = data.get('days', 7)
        name = profile.get('name', 'Student')

        # This prompt forces a high-density, metric-accurate procurement list
        prompt = f"""
        Role: Manna AI Strategic Procurement Agent.
        User: {name}
        Goal: {profile.get('goal')}
        Diet: {profile.get('diet')}
        Duration: {days} days.

        TASK: Create a foundation shopping list that maximizes nutrition and minimizes waste.
        
        ACCURACY REQUIREMENTS:
        1. **Metric Precision**: All 'amount' values must be in metric units (grams, kg, ml, liters) or specific counts (e.g., '6 Large Eggs').
        2. **The 'Why'**: Every item must have a 'why' that connects directly to the user's goal ({profile.get('goal')}).
        3. **Substitutes**: Provide a smart substitute for every item in case it is out of stock.
        4. **Zero-Waste Foundation**: Only suggest items that have multiple uses (versatile ingredients).

        OUTPUT FORMAT:
        Return ONLY a JSON array of objects with these exact keys:
        - "name": String (include an emoji 🍎)
        - "amount": String (e.g., "500g")
        - "nutrition": String (brief summary like "High Protein, Zinc")
        - "substitute": String (the backup option)
        - "why": String (the strategic reason for this item)
        """

        response = model.generate_content(prompt)
        items = clean_gemini_json(response.text)
        return jsonify(items)

    except Exception as e:
        print(f"Shopping List Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Using the port Render expects
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port) 
