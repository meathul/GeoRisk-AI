from flask import request, jsonify

from .chatbot import ClimateRiskChatbot

def routes(app):
    @app.route("/", methods=["GET"])
    def test():
        return jsonify({"response" : "server works"})
    
    chatbot = ClimateRiskChatbot()

    @app.route("/api/chat", methods=["POST"])
    def chat():
        data = request.get_json()
        query = data.get("query", "")
        if not query:
            return jsonify({"error": "Missing 'query' in request"}), 400

        response = chatbot.process_query(query)
        print(response)
        return jsonify({"response": response})
