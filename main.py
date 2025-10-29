from flask import Flask, request, jsonify, render_template_string
from schemas import Event
from session_logger import SessionLogger, serialize_entry
from llm_advisor import LLMAdvisor
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)
logger = SessionLogger()
advisor = LLMAdvisor()

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


# Simple HTML with three inputs and one output box
HTML = """
<!DOCTYPE html>
<html>
<head><title>Game Sound LLMAdvisor Demo</title></head>
<body>
<h2>Game Sound LLMAdvisor Demo UI</h2>
<form method="post">
    <label>Session Log (JSON):</label><br>
    <textarea name="sessionlog" rows="6" cols="50">{{sessionlog}}</textarea><br><br>
    <label>Current State (JSON):</label><br>
    <textarea name="currentstate" rows="3" cols="50">{{currentstate}}</textarea><br><br>
    <label>User Query:</label><br>
    <input name="userquery" type="text" size="60" value="{{userquery}}"/><br><br>
    <input type="submit" value="Ask Advisor"/>
</form>
{% if response %}
<h3>LLMAdvisor Response</h3>
<pre>{{response}}</pre>
{% endif %}
</body>
</html>
"""

@app.route('/demo', methods=['GET', 'POST'])
def demo_ui():
    sessionlog = request.form.get('sessionlog', '')
    currentstate = request.form.get('currentstate', '')
    userquery = request.form.get('userquery', '')
    response = None
    if request.method == 'POST':
        try:
            # Simple eval for demo; in real world, use json.loads and validate!
            log = eval(sessionlog) if sessionlog else None
            state = eval(currentstate) if currentstate else None
            resp = advisor.recommend(log, state, userquery)
            response = str(resp)
        except Exception as e:
            response = f"Error: {str(e)}"
    return render_template_string(HTML, sessionlog=sessionlog, currentstate=currentstate, userquery=userquery, response=response)






if __name__ == "__main__":
    app.run(debug=True, port=8080)
