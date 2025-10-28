from flask import Flask, request, jsonify
from schemas import Event
from session_logger import SessionLogger

app = Flask(__name__)
logger = SessionLogger()

@app.route("/events", methods=["POST"])
def post_event():
    data = request.json
    try:
        event = Event(**data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    entry = logger.post_event(event)
    return entry.json(), 200  # Return the entry including event + intent

@app.route("/log", methods=["GET"])
def get_log():
    return logger.to_json(), 200

if __name__ == "__main__":
    app.run(debug=True, port=8080)
