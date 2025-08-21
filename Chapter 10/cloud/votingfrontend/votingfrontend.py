import json
import sys

from talentvoting.common.acts import Act, Acts
from talentvoting.common.policy.votingpolicyengine import VotingPolicyEngine
from talentvoting.common.interfaces.voteingester import VoteIngester
from talentvoting.common.interfaces.responses import FrontendError, IneligibleVote, InvalidUser, InvalidLogin, MalformedRequest, VoteCastError
from talentvoting.common.interfaces.servicelocations import VOTE_WEB_CLIENT_DOMAIN, VOTE_QUEUE_TOPIC, PROJECT_ID

import firebase_admin
from firebase_admin import credentials, auth
from google.cloud import pubsub_v1

from flask import Flask, request, jsonify, Response, make_response
from werkzeug.exceptions import BadRequestKeyError

app = Flask(__name__)

cred = credentials.Certificate('private/serviceAccountKey.json')
firebase_admin.initialize_app(cred)

_policy_engine = VotingPolicyEngine()
publisher = pubsub_v1.PublisherClient()
# Create a path to the votes topic
topic_path = publisher.topic_path(PROJECT_ID, VOTE_QUEUE_TOPIC )

def log(message:str):
     print(message, file=sys.stderr)
  
def log_error(e:Exception, payload:str):
     print("Error: {}, Data: {}".format(str(e.__class__) + ":" + str(e), str(payload)), file=sys.stderr)
  
def _fix_response_headers(response):
    response.headers['Access-Control-Allow-Origin'] = VOTE_WEB_CLIENT_DOMAIN
    response.headers['Content-Type'] = 'text/json'

def _is_logged_in_user(user) ->bool:
     if user:
         return True
     else:
         return False
    
def _get_acts() ->Acts:
     return _policy_engine.get_all_acts()
 
def __validate_user(form) -> str:
     uid = None
     id_token = None
     try:
         id_token = form['idToken']
 
         decoded_token = auth.verify_id_token(id_token)
         # Get user information from the decoded token
         uid = decoded_token['uid']
         # Do something with the user information
         log("validateUser({})".format(uid))

         if not _is_logged_in_user(uid):
             raise  InvalidUser(uid)

         return uid

     except BadRequestKeyError:
         raise MalformedRequest("idToken")

     except InvalidUser as e:
         raise e
     
     except auth.InvalidIdTokenError:
         raise InvalidLogin(str(id_token))
     
def _record_vote(act:Act) ->any:
     try:
         log("_recordVote({})".format(act))
         # Message data must be a bytestring
         message_data = act.encode("utf-8")
         future = publisher.publish(topic_path, message_data)
         _ = future.result()

     except Exception as e:
         log_error(e, "_recordVote()")
         raise VoteCastError(str(act))

@app.route('/', methods=['POST','GET'])
def root():
     log("root {}".format(request.method))
     return "<html><body>voting front end service</body></html>"

@app.route('/vote', methods=['POST'])
def vote():
     form = request.form
     uid = __validate_user(form)

     try:
         actId = form['votedAct']
         vote = {"user": uid, "act": actId}
         vote = json.dumps(vote)
         log("vote({}".format(vote))
         _record_vote(vote)
         response = make_response(vote, 200)
         _fix_response_headers(response)
         log("response data: {}".format(str(response.get_data())))
         log("response headers: {}".format(str(response.headers)))
         return response
     except BadRequestKeyError:
         error = {"error" : str(MalformedRequest("votedAct").response()[0])}    
         error = json.dumps(error)
         log_error(error, "error:vote()")
         response = make_response(error, error.response()[1])
         _fix_response_headers(response)
         log("response data: {}".format(str(response.get_data())))
         log("response headers: {}".format(str(response.headers)))
         return response
     
     except FrontendError as e:
         error = {"error" : str(e.response()[0])}    
         error = json.dumps(error)
         log_error(error, "error:vote()")
         response = make_response(error, e.response()[1])
         _fix_response_headers(response)
         log("response data: {}".format(str(response.get_data())))
         log("response headers: {}".format(str(response.headers)))
         return response


@app.route('/getActs', methods=['POST'])
def get_eligible_acts() ->any:
     try:
         form = request.form
         uid = __validate_user(form)

         candidate_acts = _get_acts()
         acts = {"acts" : candidate_acts}  # was eligible_acts
         acts = json.dumps(acts)
        
         log("getActs({})".format(acts))
         response = make_response(acts, 200)
         _fix_response_headers(response)
         log("response data: {}".format(str(response.get_data())))
         log("response headers: {}".format(str(response.headers)))
         return response
     
     except FrontendError as e:
         error = {"error" : str(e.response()[0])}    
         error = json.dumps(error)
         log_error(error, "error:getActs()")
         response = make_response(error, e.response()[1])
         _fix_response_headers(response)
         log("response data: {}".format(str(response.get_data())))
         log("response headers: {}".format(str(response.headers)))
         return response