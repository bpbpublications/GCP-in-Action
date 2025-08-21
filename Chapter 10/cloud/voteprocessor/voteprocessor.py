import json
from flask import Flask, request
app = Flask(__name__)


def _process_vote(message:json) -> bool:
    """
    Process a JSON message containing a vote.
    args:
        message: A JSON dict
    Returns:
        True if a message was processed, False otherwise
    """
    if not message:
        return False
    if not isinstance(message, dict):
        return False
    if "user" not in message or "act" not in message:
        return False
    return True



@app.route("/", methods=["POST"])
def index():
    """Receive a Pub/Sub message which should contain valid JSON and issue HTTP response."""
    message = request.data
   
    print("incoming message!")
    if message:
        print("data: {}".format(message))
    try:
        vote = json.loads(message)
        if _process_vote(vote):
            print("Processed vote: {}".format(vote))
        else:
            print("Invalid vote: {}".format(vote))
            return ("Invalid vote", 400)  # Invalid content error status  
    except ValueError as e:
        print("Invalid JSON received: {}".format(e))
        return ("Invalid JSON", 400)
    except Exception as e:
        print("error: {}".format(e))
        return ("", 500)  # Internal server error status
    return ("", 204)  # No content OK status