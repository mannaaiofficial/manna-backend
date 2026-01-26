import os
import google.generativeai as genai
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------
# 🔑 PASTE YOUR GOOGLE KEY BELOW (Inside the quotes)
# ---------------------------------------------------------
# Paste the key that starts with "AI..." inside the quotes
genai.configure(api_key="AIzaSyBEluOv_MAC0JD6B6MR_BQv69HM8vjqcEY") 

# Set up the model
model = genai.GenerativeModel('gemini-2.5-flash-lite')

print("📢 GOOGLE GEMINI (FREE) IS RUNNING on Port 5001")

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/<path:path>', methods=['GET', 'POST'])
def generate_magic(path):
    print(f"📢 REQUEST RECEIVED for: {path}")
    print("🧠 Google Gemini is thinking...")

    try:
        # Ask Google for the plan
        response = model.generate_content(
            "You are a meal planner. Generate a simple 3-day meal plan with a shopping list. Return ONLY valid JSON text, no markdown formatting."
        )
        
        # Get the answer
        ai_reply = response.text
        
        # Clean up if Google adds ```json marks (common with Gemini)
        ai_reply = ai_reply.replace("```json", "").replace("```", "")
        
        print("✅ AI Finished!")
        return jsonify({"success": True, "data": ai_reply})

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)