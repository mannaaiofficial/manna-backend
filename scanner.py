import google.generativeai as genai
import PIL.Image
import json

# --- 1. SETUP ---
# Paste your NEW API Key below
GOOGLE_API_KEY = "AIzaSyBEluOv_MAC0JD6B6MR_BQv69HM8vjqcEY"
genai.configure(api_key=GOOGLE_API_KEY)

# We are using the name that appeared in your list:
model = genai.GenerativeModel('gemini-flash-latest')

def scan_fridge():
    print("📸 Scanning your fridge photo...")

    # 2. OPEN THE FRIDGE
    try:
        img = PIL.Image.open('fridge.jpg')
    except:
        print("❌ ERROR: I cannot find 'fridge.jpg'. Make sure the photo is in this folder!")
        return

    # 3. ASK THE AI
    print("🤖 Analyzing food & nutrition...")
    prompt = """
    Look at this photo.
    1. List every food item you see.
    2. Estimate the calories per serving.
    3. Estimate the protein per serving.

    Format the output as a clean list of JSON data like this:
    [
      {"item": "Apple", "calories": 95, "protein": "0.5g"},
      {"item": "Greek Yogurt", "calories": 100, "protein": "10g"}
    ]
    Return ONLY the JSON list.
    """

    try:
        response = model.generate_content([prompt, img])
        
        # 4. SHOW RESULTS
        print("\n✅ --- DETECTED ITEMS ---")
        # We clean the text to make sure it looks nice
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        print(clean_text)
        
    except Exception as e:
        print(f"❌ Error details: {e}")

# Run the function
scan_fridge()