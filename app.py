from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

JIRA_BASE_URL = os.environ.get("JIRA_BASE_URL")
JIRA_EMAIL = os.environ.get("JIRA_EMAIL")
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN")
API_SHARED_SECRET = os.environ.get("API_SHARED_SECRET")


def check_auth():
    provided = request.headers.get("X-Api-Key")
    return provided == API_SHARED_SECRET


def send_jira_comment(issue_key, message):
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/comment"
    body = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": message}]
                }
            ]
        }
    }
    response = requests.post(
        url,
        json=body,
        auth=(JIRA_EMAIL, JIRA_API_TOKEN),
        headers={"Content-Type": "application/json"},
        verify=False
    )
    response.raise_for_status()
    return response.json()


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/notify", methods=["POST"])
def notify():
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    if not data or "issueKey" not in data or "message" not in data:
        return jsonify({"error": "issueKey and message are required"}), 400

    try:
        result = send_jira_comment(data["issueKey"], data["message"])
        return jsonify({"status": "sent", "result": result}), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
