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
        "instructions (step-by-step), and a relevant Unsplash image URL.UNIT CONSISTENCY: You MUST use the same 'unit' and 'name' provided in the user's inventory JSON."
        
    )
)

# --- 2. THE CLEANER ---
def clean_gemini_json(text):
    """Bulletproof filter to extract JSON even if the AI adds chatter."""
    try:
        # 1. Remove markdown code blocks if they exist
        clean = text.replace("```json", "").replace("```", "").strip()
        
        # 2. Find the FIRST '[' and the LAST ']'
        start = clean.find("[")
        end = clean.rfind("]")
        
        if start != -1 and end != -1:
            json_str = clean[start:end + 1]
            return json.loads(json_str)
        
        # 3. Fallback: If it's an object with a 'recipes' key instead of a list
        start_obj = clean.find("{")
        end_obj = clean.rfind("}")
        if start_obj != -1:
            data = json.loads(clean[start_obj:end_obj + 1])
            return data.get('recipes', data) # Return the list inside or the object
            
        return []
    except Exception as e:
        print(f"CRITICAL CLEANER ERROR: {e}")
        print(f"RAW TEXT THAT FAILED: {text[:200]}...") # See the first 200 chars
        return []

# --- 3. THE BIO-CALCULATOR (FINAL MVP VERSION) ---
def get_caloric_needs(data):
    """
    Calculates exact caloric and protein needs using the Mifflin-St Jeor Equation.
    This is the 'brain' that ensures accuracy for different body types.
    """
    try:
        # Extract data with safe defaults for a young student
        weight = float(data.get('weight', 70))
        height = float(data.get('height', 170))
        age = int(data.get('age', 20))
        gender = data.get('gender', 'female').lower()
        activity = data.get('activityLevel', 'moderate').lower()
        goal = data.get('goal', 'energy').lower()

        # 1. Calculate Basal Metabolic Rate (BMR)
        if gender == 'male':
            bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
        else:
            bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161

        # 2. Apply Activity Multiplier (TDEE)
        multipliers = {
            'sedentary': 1.2, 
            'moderate': 1.55, 
            'active': 1.725, 
            'athlete': 1.9
        }
        tdee = bmr * multipliers.get(activity, 1.2)

        # 3. Goal Adjustment & Protein Scaling
        if "loss" in goal or "weight" in goal:
            calories = tdee - 500
            protein = weight * 2.0  # Higher protein helps with satiety during loss
        elif "muscle" in goal or "bulk" in goal:
            calories = tdee + 400
            protein = weight * 2.2  # Max protein for muscle synthesis
        else:
            calories = tdee
            protein = weight * 1.6  # Maintenance baseline

        return round(calories), round(protein)

    except Exception as e:
        print(f"Bio-Calculator Error: {e}")
        return 2000, 130 # Safe fallback for standard student needs
# --- 4. ROUTES ---

@app.route('/')
def home():
    return "Manna AI Server is Online!"

@app.route('/api/recipes', methods=['POST'])
def generate_recipes():
    try:
        data = request.json
inventory = data.get('inventory', []) # Remove comma
profile = data.get('userProfile', {})  # Remove comma
vibe = profile.get('vibe', 'Speed')    # Remove comma
days_left = int(profile.get('daysRemaining', 7)) # Remove comma

# This line is perfect as is
target_cals, target_protein = get_caloric_needs(profile)
        # We use .format() instead of an f-string to avoid the "Invalid format specifier" error
        prompt = """
        Role: Manna AI Master Chef & Resource Manager
        Mission: Create amazing, healthy meals using ONLY provided inventory that will last the user the perfect amount of time.
        
        User Profile: {user_profile}
        Daily Target: {target_cals}
        Current Inventory: {inventory_data}
        Target Cooking Vibe: {vibe_style}
        Days until next shop: {days} days.

        TASK: 
1. MANDATORY RATIONING: You must calculate a budget for every ingredient: (Total Quantity ÷ {days} days). 
   The 'amountValue' for EACH recipe MUST be less than or equal to this daily budget. 
   *Example: If user has 500g Beef and 5 days left, 'amountValue' for one recipe cannot exceed 100g.*
2. MATCHING: The 'name' and 'unit' must be an EXACT string match to the inventory data provided.
3. DATA TYPE: The 'amountValue' must be a raw Number, not a string.
4. CULINARY ROUNDING: Use human-friendly numbers. Round grams to the nearest 50g (e.g., 150g, 200g). For pieces/units, use whole numbers or halves (e.g., 1 lemon, 0.5 onion). NEVER output more than one decimal point."
       
        STRICT CONSTRAINTS:
        1. NO EXTERNAL INGREDIENTS: Use only items from the Inventory. (Salt, Pepper, Water, and 1 Oil allowed). 
        2. DIETARY PURITY: Strictly follow the diet specified in the profile.
        3. ZERO-WASTE PRIORITY: Focus on using up expiring items first.

        OUTPUT FORMAT:
        Return ONLY a JSON list of 3 recipe objects. Each must have:
        - "id": unique string
        - "title": appetizing name
        - "description": description
        - "calories": number
        - "macros": {{ "p": number, "c": number, "f": number }}
        - "time": string
        - "ingredients": [
            {{ 
              "name": "match inventory exactly", 
              "amount": "150g", 
              "amountValue": 150, 
              "unit": "g" 
            }}
          ]
        - "instructions": [string steps]
        - "image": "https://images.unsplash.com/photo-[ID]?w=800&q=80"
        """.format(
            user_profile=json.dumps(profile),
            inventory_data=json.dumps(inventory),
            vibe_style=vibe,
            days=days_left
            Daily Target: {target_cals}
        )

        # Use the model with the system_instruction configured earlier
        response = model.generate_content(prompt)
        
        # Clean and validate the JSON
        recipes = clean_gemini_json(response.text)
        
        return jsonify(recipes)

    except Exception as e:
        print(f"Error in Recipe Generation: {e}")
        return jsonify({"error": str(e)}), 500

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
        days = int(data.get('days', 7))
        name = profile.get('name', 'Student')

        target_cals, target_protein = get_caloric_needs(profile)
        total_period_cals = target_cals * days
        total_protein_g = target_protein * days
        # Calculate rough carb quota (approx 45% of energy)
        total_carbs_g = round(((target_cals * 0.45) / 4) * days)

        # This prompt forces a high-density, metric-accurate procurement list
        prompt = f"""
        Role: Manna AI Strategic Procurement Agent.
        User: {name}
        Goal: {profile.get('goal')}
        Diet: {profile.get('diet')}
        Duration: {days} days.

        PRECISION LOGISTICS:
        - Background Daily Target: {target_cals} kcal/day.
        - Total Period Target: {total_period_cals} total calories.
        - Required Protein Volume: Total of {total_protein_g}g from all protein sources.
        - Required Carb Volume: Total of {total_carbs_g}g from all grain/starch sources.

        TASK: Create a foundation shopping list that maximizes nutrition, fulfills these exact caloric needs, and minimizes waste.
        
        ACCURACY REQUIREMENTS:
        1. **Metric Precision**: All 'amount' values must be in metric units (grams, kg, ml, liters) or specific counts (e.g., '6 Large Eggs').
        2. **The 'Why'**: Every item must have a 'why' that connects directly to the user's goal ({profile.get('goal')}).
        3. **Substitutes**: Provide a smart substitute for every item in case it is out of stock.
        4. **Zero-Waste Foundation**: Only suggest items that have multiple uses (versatile ingredients).
        5. **Logistical Sizing**: Scale the 'amount' of staples so the total volume of food is appropriate for a {days}-day period for someone with the user's goal. (Background target: {target_cals} kcal/day).
        6. **Retail Scaling**: Round all amounts to standard supermarket sizes (e.g., 250g, 500g, 1kg, 1L). No weird decimals like "1.14kg."
        7. **STRATEGIC VARIETY**: Do NOT suggest huge bulk amounts of a single item (e.g., avoid 1kg of broccoli). Instead, prioritize a diverse range of ingredients in smaller, realistic portions (e.g., 200g-400g for veggies) to ensure the user doesn't get bored and the meals are varied.
        
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
        
@app.route('/api/inventory/update', methods=['POST'])
def update_inventory():
    try:
        data = request.json
        current_inventory = data.get('inventory', [])
        cooked_recipe = data.get('recipe', {})
        ingredients_used = cooked_recipe.get('ingredients', [])

        # Convert current inventory to a dictionary for easier lookup by name
        inv_dict = {item['name']: item for item in current_inventory}
        low_stock_items = []

        for used_item in ingredients_used:
            name = used_item.get('name')
            # Use the precise amountValue from the AI's recipe
            used_qty = float(used_item.get('amountValue', 0))

            if name in inv_dict:
                old_qty = float(inv_dict[name].get('quantity', 0))
                new_qty = max(0, old_qty - used_qty)
                
                # Update the quantity in the dictionary
                inv_dict[name]['quantity'] = round(new_qty, 2)

                # Identify if the item is now low or empty
                if new_qty <= (old_qty * 0.2) or new_qty == 0:
                    low_stock_items.append(name)

        # Remove items that are now at 0 from the list
        final_inventory = [v for k, v in inv_dict.items() if v['quantity'] > 0]

        return jsonify({
            "success": True,
            "updatedInventory": final_inventory,
            "lowStock": low_stock_items
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Using the port Render expects
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port) 


