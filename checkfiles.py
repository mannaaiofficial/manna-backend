import google.generativeai as genai
import os

# Configure the API key exactly like backend.py does
genai.configure(api_key=os.environ.get("AIzaSyBEluOv_MAC0JD6B6MR_BQv69HM8vjqcEY"))

print("--- ASKING GOOGLE FOR AVAILABLE MODELS ---")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"FOUND: {m.name}")
except Exception as e:
    print(f"ERROR: {e}")
print("--- END OF LIST ---")