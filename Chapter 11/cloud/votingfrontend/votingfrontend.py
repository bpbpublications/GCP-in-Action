import json
import sys
from typing import List, Tuple

from talentvoting.common.acts import Act, Acts, parse_act
from talentvoting.common.policy.votingpolicyengine import DefaultPolicyEngine
from talentvoting.common.interfaces.voteingester import VoteIngester
from talentvoting.common.interfaces.responses import FrontendError, IneligibleVote,\
      InvalidUser, InvalidLogin, MalformedRequest, VoteCastError, VoteHistoryError
from talentvoting.common.interfaces.servicelocations import VOTE_WEB_CLIENT_DOMAIN, \
    VOTE_QUEUE_TOPIC, PROJECT_ID
from talentvoting.cloud.common.votingdatabaseutils import get_database

import firebase_admin
from firebase_admin import credentials, auth
from google.cloud import pubsub_v1

from flask import Flask, request, jsonify, Response, make_response
from werkzeug.exceptions import BadRequestKeyError

app = Flask(__name__)

cred = credentials.Certificate('private/serviceAccountKey.json')
firebase_admin.initialize_app(cred)

publisher = pubsub_v1.PublisherClient()
# Create a path to the votes topic
topic_path = publisher.topic_path(PROJECT_ID, VOTE_QUEUE_TOPIC )


def log(message:str):
     print(message, file=sys.stderr)
  

def log_error(e:Exception, payload:str):
     print("Error: {}, Data: {}".format(str(e.__class__) + ":" + str(e), str(payload)), 
           file=sys.stderr)
  

def _fix_response_headers(response):
    "Add needed headers to the response."
    response.headers['Access-Control-Allow-Origin'] = VOTE_WEB_CLIENT_DOMAIN
    response.headers['Content-Type'] = 'text/json'


def _is_user_logged_in(user) ->bool:
     "If the user is defined, we assume it to be a valid logged in user."
     if user:
         return True
     else:
         return False


def __get_user_vote_history(db_connection, \
                         user_id:str, round_id:int)->Tuple[int,List[str]]:
    "Return the array of voting history for this user in this round."
    result_rows = db_connection.execute_sql(
        "SELECT Total_votes_cast, voted_acts from Votebudget "+
        "WHERE Userid = '{}' and Round_id = {}".format(user_id, round_id)
    )
    result = result_rows.one_or_none()
    if result:
        log("votebudget(total,history):{} [1]:{}".format(result[0], result[1]))
        prev_total = result[0]
        prev_votes = result[1]
    else:
        return (None, None)

    return (prev_total, prev_votes)


def _get_acts(vote_history:List[str]) ->Acts:
     "Return the current JSON map of acts, marked as eligible or not for voting."
     acts = DefaultPolicyEngine.get_all_acts()
     for act in acts:
         round_id, act_number = parse_act(act["act"])
         log("checking round,act: {},{}".format(round_id, act_number))
         if DefaultPolicyEngine.is_eligible_vote(round_id, act_number, vote_history):
             log("voting_eligible")
             act["voting_eligible"] = True
         else:
             log("not voting_eligible")
             act["voting_eligible"] = False
     return acts
 
def __validate_user(form) -> str:
     "Extract the uid from the id_token in the request."
     uid = None
     id_token = None
     try:
         id_token = form['idToken']
 
         # Get user information from the decoded token
         decoded_token = auth.verify_id_token(id_token)
         uid = decoded_token['uid']

         if not _is_user_logged_in(uid):
             raise  InvalidUser(uid)

         return uid
     except BadRequestKeyError:
         raise MalformedRequest("idToken")
     except InvalidUser as e:
         raise e
     except auth.InvalidIdTokenError:
         raise InvalidLogin(str(id_token))


def _record_vote(act:Act) ->any:
     "Publish the vote to the Pub/Sub topic."
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
     "Request handler for vote endpoint."
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
     "Request handler for getActs endpoint."
     try:
         form = request.form
         uid = __validate_user(form)
         vote_history = []
         round_id = DefaultPolicyEngine.get_current_round_id()
         with get_database().snapshot() as db_connection:
             _, fetched_vote_history = __get_user_vote_history(db_connection, 
                                                            uid, round_id)
         if fetched_vote_history == None:
             raise VoteHistoryError(uid, round_id)
         candidate_acts = _get_acts(fetched_vote_history)

         log("fetched_vote_history: {}".format(fetched_vote_history))

         acts_bundle = {
             "acts_bundle" : {"acts" : candidate_acts,
                              "vote_history" : fetched_vote_history,
                              "vote_limit": DefaultPolicyEngine.MAX_VOTES_PER_ROUND}
                              }
         acts_bundle = json.dumps(acts_bundle)

         log("getActs({})".format((acts_bundle)))
         response = make_response(acts_bundle, 200)
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