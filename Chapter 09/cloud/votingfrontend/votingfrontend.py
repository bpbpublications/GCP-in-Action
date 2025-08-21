from talentvoting.common.acts import Act, Acts
from talentvoting.common.policy.votingpolicyengine import VotingPolicyEngine
from talentvoting.common.interfaces.voteingester import VoteIngester
from talentvoting.common.interfaces.responses import FrontendError, IneligibleVote, InvalidUser, InvalidLogin, MalformedRequest
from talentvoting.common.interfaces.servicelocations import VOTE_WEB_CLIENT_DOMAIN

import firebase_admin
from firebase_admin import credentials, auth

from flask import Flask, request, jsonify, Response, make_response

import json

app = Flask(__name__)

from werkzeug.exceptions import BadRequestKeyError

import sys

cred = credentials.Certificate('private/serviceAccountKey.json')
firebase_admin.initialize_app(cred)

_policy_engine = VotingPolicyEngine()

def log(e:Exception, payload:str):
     print("Message: {}, Data: {}".format(str(e.__class__) + ":" + str(e), str(payload)), file=sys.stderr)
  
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
 
def validate_user(form) -> str:
     uid = None
     id_token = None
     try:
         id_token = form['idToken']
 
         decoded_token = auth.verify_id_token(id_token)
         # Get user information from the decoded token
         uid = decoded_token['uid']
         # Do something with the user information
         log({'success': True, 'uid': uid},"validateUser()")

         if not _is_logged_in_user(uid):
             raise  InvalidUser(uid)

         return uid

     except BadRequestKeyError:
         raise MalformedRequest("idToken")

     except InvalidUser as e:
         raise e
     
     except auth.InvalidIdTokenError:
         raise InvalidLogin(str(id_token))
     
@app.route('/', methods=['POST','GET'])
def root():
     log(str(request.form), "root" )
     return "<html><body>voting front end service</body></html>"

@app.route('/vote', methods=['POST'])
def vote():
     form = request.form
     try:
         actId = form['votedAct']
         act = {"act":  actId}
         act = json.dumps(act)
         log(act, "vote()")
         response = make_response(act, 200)
         _fix_response_headers(response)
         log(str(response.get_data()), 'response data')
         log(str(response.headers), 'response headers')
         return response
     except BadRequestKeyError:
         error = {"error" : str(MalformedRequest("votedAct").response()[0])}    
         error = json.dumps(error)
         log(error, "error:vote()")
         response = make_response(error, error.response()[1])
         _fix_response_headers(response)
         log(str(response.get_data()), 'error response data')
         log(str(response.headers), 'response headers')
         return response


@app.route('/getActs', methods=['POST'])
def get_eligible_acts() ->any:
     try:
         form = request.form
         uid = validate_user(form)

         candidate_acts = _get_acts()
         acts = {"acts" : candidate_acts}  # was eligible_acts
         acts = json.dumps(acts)
        
         log(acts, "getActs()")
         response = make_response(acts, 200)
         _fix_response_headers(response)
         log(str(response.get_data()), 'response data')
         log(str(response.headers), 'response headers')
         return response
     
     except FrontendError as e:
         error = {"error" : str(e.response()[0])}    
         error = json.dumps(error)
         log(error, "error:getActs()")
         response = make_response(error, e.response()[1])
         _fix_response_headers(response)
         log(str(response.get_data()), 'error response data')
         log(str(response.headers), 'response headers')
         return response
