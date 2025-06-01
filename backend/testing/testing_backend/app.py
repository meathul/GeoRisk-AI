from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow requests from frontend

last_message = ""  # Store the last message

@app.route('/api/chat', methods=['POST'])
def chat():
    global last_message
    data = request.json
    user_message = data.get('message', '')
    last_message = user_message  # Save the last message
    response = {
        "reply": f"You said: {user_message}"
    }
    return jsonify(response)

@app.route('/')
def index():
    return f"<h2>Last message from frontend:</h2><p>{last_message or 'No message yet.'}</p>"

if __name__ == '__main__':
    app.run(debug=True)