from flask import Flask, request, jsonify
from schemas import Event
from session_logger import SessionLogger, serialize_entry
from llm_advisor import LLMAdvisor

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

@app.route("/replay", methods=["POST"])
def replay():
    event_dicts = request.json
    replayed = logger.replay_log(event_dicts)
    # Use serialize_entry to make replayed log fully JSON serializable
    return jsonify([serialize_entry(entry) for entry in replayed]), 200

@app.route("/kpi", methods=["GET"])
def report():
    # Returns KPI stats for current session
    return jsonify(logger.kpi_report()), 200

@app.route("/advisor", methods=["POST"])
def advisor_route():
    data = request.json
    session_log = data.get("session_log", [])
    current_state = data.get("current_state", {})
    user_query = data.get("user_query")

    advisor = LLMAdvisor()
    recommendation = advisor.recommend(session_log, current_state, user_query)
    return jsonify(recommendation), 200







if __name__ == "__main__":
    app.run(debug=True, port=8080)
