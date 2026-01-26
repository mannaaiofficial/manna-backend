import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------
# 🔑 PASTE YOUR OPENAI API KEY BELOW (Inside the quotes)
# ---------------------------------------------------------
client = OpenAI(api_key="AIzaSyBEluOv_MAC0JD6B6MR_BQv69HM8vjqcEY") 

print("🔥 REAL AI SERVER RUNNING on Port 5001")

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/<path:path>', methods=['GET', 'POST'])
def generate_magic(path):
    print(f"📢 REQUEST RECEIVED for: {path}")
    print("🧠 The AI is thinking... (This might take 10 seconds)")

    try:
        # This tells the AI what to do
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful meal planner."},
                {"role": "user", "content": "Generate a simple 3-day meal plan with a shopping list. Return ONLY valid JSON."}
            ]
        )
        
        # Get the answer
        ai_reply = response.choices[0].message.content
        print("✅ AI Finished!")
        
        # Send it to the phone
        return jsonify({"success": True, "data": ai_reply})

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)