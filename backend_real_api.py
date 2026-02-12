import os
import json
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
import PIL.Image
from datetime import datetime

# --- 1. CONFIGURATION ---
app = Flask(__name__)
CORS(app)

# Use Environment Variable for security
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

current_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(current_dir, 'ingredients_master.json')

with open(json_path, 'r') as f:
    INGREDIENTS_MASTER = json.load(f)

print(f"✅ Loaded {len(INGREDIENTS_MASTER)} master ingredients.")

model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    generation_config={"response_mime_type": "application/json"},
    system_instruction=(
        "You are the Manna AI Kitchen Engine. Your mission is to help individuals eat amazing, healthy meals while wasting nothing. You must turn limited inventory into high-quality culinary experiences.\n\n"
        "STRICT OPERATIONAL RULES:\n"
        "1. ZERO HALLUCINATIONS: You are strictly forbidden from using any item that is not currently in the inventory_data. Use the MASTER DATABASE ONLY to look up the 'substitute', 'shelf-life', or 'nutritional data' of items already present in the user inventory. If the user does not have an item in their inventory, you ARE FORBIDDEN from including it in a recipe.\n"
        "2. ACCURACY & DIET: Strictly adhere to the user's dietary style (e.g., Vegan, Pescatarian). "
        "If a recipe traditionally requires a non-compliant ingredient, do not suggest it unless "
        "a suitable substitute exists in their inventory.\n"
        "3. VIBE-DRIVEN LOGIC: Adapt the complexity and tone of instructions to the 'cookingVibe':\n"
        "   - 'Speed': Max 15 mins, 1 pan, high efficiency.\n"
        "   - 'Therapy': Focus on mindful preparation, chopping skills, and relaxation.\n"
        "   - 'Pro': Focus on plating, sauce reductions, and advanced flavor balancing.\n"
        "4. WASTE REDUCTION: For every generation, prioritize the item with the lowest 'daysLeft' value.\n"
        "5. OUTPUT FORMAT: Return ONLY ONE high-quality JSON recipe object that matches the requested 'mealType' (Breakfast, Lunch, or Dinner). The description must explain why this specific meal was chosen for the user's current goal and vibe.\n"
        "6. RATIONING LOGIC: You are a resource manager. Check 'daysRemaining'. "
        "Proportionally divide ingredients so the user does not run out of food before their next shop. "
        "For example, if they have 1kg of meat for 5 days, suggest 200g per recipe, not 500g."
        "id, title, description, calories, macros (p, c, f), time, ingredients (name and amount), "
        "instructions (step-by-step), and a relevant Unsplash image URL. UNIT CONSISTENCY: You MUST use the same 'unit' and 'name' provided in the user's inventory JSON."
    )
)

def clean_gemini_json(text):
    try:
        text = text.replace("```json", "").replace("```", "").strip()
        start_idx = text.find("{") if text.find("{") != -1 else text.find("[")
        if start_idx == -1: return {"error": "No JSON found"}
        content = text[start_idx:]
        decoder = json.JSONDecoder()
        data, end_pos = decoder.raw_decode(content)
        return data
    except Exception as e:
        print(f"CLEANER CRASH: {e}")
        return {"error": "Invalid structure"}

def get_caloric_needs(data):
    try:
        weight = float(data.get('weight', 70))
        height = float(data.get('height', 170))
        age = int(data.get('age', 20))
        gender = data.get('gender', 'female').lower()
        activity = data.get('activityLevel', 'moderate').lower()
        goal = data.get('goal', 'energy').lower()

        if gender == 'male':
            bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
        else:
            bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161

        multipliers = {'sedentary': 1.2, 'moderate': 1.55, 'active': 1.725, 'athlete': 1.9}
        tdee = bmr * multipliers.get(activity, 1.2)

        if "loss" in goal or "weight" in goal:
            calories, protein = tdee - 500, weight * 2.0
        elif "muscle" in goal or "bulk" in goal:
            calories, protein = tdee + 400, weight * 2.2
        else:
            calories, protein = tdee, weight * 1.6

        return round(calories), round(protein)
    except Exception as e:
        print(f"Bio-Calculator Error: {e}")
        return 2000, 130

# --- ROUTES ---

@app.route('/')
def home():
    return "Manna AI Server is Online!"

@app.route('/api/recipes', methods=['POST'])
def generate_recipes():
    try:
        data = request.json
        inventory = data.get('inventory', [])
        relevant_master_data = [
            m for m in INGREDIENTS_MASTER 
            if any(i['name'].lower() in m['name'].lower() for i in inventory)
        ]
        profile = data.get('userProfile', {})
        vibe = profile.get('vibe', 'Speed')
        days_left = int(profile.get('daysRemaining', 7)) 
        tastes = profile.get('tastes', {})
        target_cals, target_protein = get_caloric_needs(profile)
        
        prompt = """
        Role: Manna AI Master Chef & Resource Manager
        Mission: Create a FULL DAY of amazing, healthy meals (Breakfast, Lunch, and Dinner) using ONLY provided inventory.
        
        STRICT MASTER DATABASE: {master_db}

        TASK: You MUST ONLY use items from the MASTER DATABASE. 
        
        User Profile: {user_profile}
        Daily Target: {target_cals}
        Current Inventory: {inventory_data}
        Target Cooking Vibe: {vibe_style}
        Days until next shop: {days} days.

        STRICT OPERATIONAL RULES:
        1. MANDATORY RATIONING: Divide ingredients across the three meals so the user doesn't run out. Budget = (Total Quantity ÷ {days} days).
        2. MATCHING: The 'name' and 'unit' must be an EXACT string match to the inventory.
        3. DATA TYPE: The 'amountValue' must be a raw Number.
        4. ZERO-WASTE PRIORITY: Prioritize items with 'daysLeft' <= 2. They MUST be used today.
        5. PALATE ALIGNMENT: User tastes are {tastes}. 
        6. MEAL CONTEXT: Respect the 'breakfastStyle' preference for the breakfast object.

        OUTPUT FORMAT:
        Return ONLY a single JSON object with exactly three keys: "breakfast", "lunch", and "dinner". 
        Each key must contain a recipe object structured like this:
        {{
            "id": "unique string",
            "title": "appetizing name",
            "description": "Why this was chosen for their goal/vibe.",
            "calories": number,
            "macros": {{ "p": number, "c": number, "f": number }},
            "time": "string",
            "ingredients": [
                {{ "name": "match inventory", "amount": "150g", "amountValue": 150, "unit": "g" }}
              ],
            "instructions": ["step 1", "step 2"],
            "image": "https://images.unsplash.com/photo-[ID]?w=800&q=80"
        }}
        """.format(
            master_db=json.dumps(relevant_master_data),          
            user_profile=json.dumps(profile),
            inventory_data=json.dumps(inventory),
            vibe_style=vibe,
            days=days_left,
            target_cals=target_cals,
            tastes=json.dumps(tastes)
        )

        response = model.generate_content(prompt)
        daily_plan = clean_gemini_json(response.text)
        
        requested_meal = data.get('mealType')
        if requested_meal and requested_meal in daily_plan:
            return jsonify(daily_plan[requested_meal])
            
        return jsonify(daily_plan)

    except Exception as e:
        print(f"Error in Recipe Generation: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/shop', methods=['POST'])
def generate_shopping_list():
    try:
        data = request.json
        profile = data.get('userProfile', {})
        days = int(data.get('days', 7))
        name = profile.get('name', 'Student')
        tastes = profile.get('tastes', {})

        target_cals, target_protein = get_caloric_needs(profile)
        total_period_cals = target_cals * days
        total_protein_g = target_protein * days
        total_carbs_g = round(((target_cals * 0.45) / 4) * days)

        prompt = """
        You are Manna AI, a strategic kitchen operator.
        MASTER DATABASE: {master_db}

        TASK: When generating ingredients or recipes, you MUST ONLY use items from the MASTER DATABASE. 
        If an item is not in the database, use the 'substitute' listed in the database instead.

        Role: Manna AI Strategic Procurement Agent.
        User: {name}, Goal: {goal}, Diet: {diet}, Duration: {days} days.
        Taste Profile: {tastes_json}

        PRECISION LOGISTICS:
        - Background Daily Target: {target_cals} kcal/day.
        - Total Period Target: {period_cals} total calories.
        - Required Protein Volume: Total of {protein_g}g from all protein sources.
        - Required Carb Volume: Total of {carbs_g}g from all grain/starch sources.

        STRICT TASTE ENFORCEMENT:
        1. Flavor Alignment: You MUST include at least 3 specific aromatics or condiments matching Craved Flavors.
        2. Seasoning Level: If 'Bold', include at least 2 dry spices or fresh herbs.
        3. Breakfast Logic: If 'Savory', prioritize proteins. If 'Sweet', prioritize grains.

        TASK: Create a foundation shopping list.
        The 'Diverse Pantry' Rule: No single starch > 40% of total carbs.
        Unit Caps: Limit staples to 500g max. Force variety.
        BOREDOM IS A FAILURE: If the list looks like a survival kit, you have failed.
        THE RAINBOW RULE: Suggest at least 4 different colored vegetables.

        ACCURACY REQUIREMENTS:
        1. Metric Precision: amounts in grams, kg, ml, liters.
        2. The 'Why': Connect every item to {goal}.
        3. Substitutes: Provide one for every item.

        OUTPUT FORMAT:
        Return ONLY a JSON array of objects with these keys:
        [
          {{
            "name": "String (include emoji 🍎)",
            "amount": "500g",
            "nutrition": "High Protein",
            "substitute": "String",
            "why": "String"
          }}
        ]
        """.format(
            master_db=json.dumps(INGREDIENTS_MASTER),
            name=name,
            goal=profile.get('goal'),
            diet=profile.get('diet'),
            days=days,
            tastes_json=json.dumps(tastes),
            target_cals=target_cals,
            period_cals=total_period_cals,
            protein_g=total_protein_g,
            carbs_g=total_carbs_g
        )

        response = model.generate_content(prompt)
        items = clean_gemini_json(response.text)
        
        if isinstance(items, dict) and "items" in items:
            items = items["items"]
            
        return jsonify(items)

    except Exception as e:
        print(f"Shopping List Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/inventory/update', methods=['POST'])
def update_inventory():
    try:
        data = request.json
        current_inventory = data.get('inventory', [])
        cooked_recipe = data.get('recipe', {})
        ingredients_used = cooked_recipe.get('ingredients', [])
        low_stock_items = []
        
        for used_item in ingredients_used:
            used_name = used_item.get('name', '').lower().strip()
            used_qty = float(used_item.get('amountValue', 0))

            for inventory_item in current_inventory:
                inventory_name = inventory_item.get('name', '').lower().strip()
                if used_name in inventory_name or inventory_name in used_name:
                    old_qty = float(inventory_item.get('quantity', 0))
                    new_qty = max(0, old_qty - used_qty)
                    inventory_item['quantity'] = round(new_qty, 2)
                    if 0 < new_qty <= (old_qty * 0.2):
                        low_stock_items.append(inventory_item['name'])
                    break 

        final_inventory = [item for item in current_inventory if float(item.get('quantity', 0)) > 0.01]
        return jsonify({
            "success": True,
            "updatedInventory": final_inventory,
            "lowStock": list(set(low_stock_items))
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
