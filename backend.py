from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

print("📢 VERIFICATION: I AM THE UNIVERSAL SERVER")

# --- THE MAGIC CATCH-ALL ---
# This tells Python: "Answer ANY request, no matter the name."
@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/<path:path>', methods=['GET', 'POST'])
def catch_all(path):
    print(f"📢 PHONE CONNECTED to: /{path}")
    
    return jsonify([
        {"name": "UNIVERSAL COOKIE", "quantity": "Infinite"},
        {"name": "The Connection Works", "quantity": "100%"}
    ])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)