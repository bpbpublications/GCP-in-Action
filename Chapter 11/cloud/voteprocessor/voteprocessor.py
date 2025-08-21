import json
from flask import Flask, request
from talentvoting.common.policy.votingpolicyengine import  DefaultPolicyEngine
from talentvoting.cloud.common.votingdatabaseutils import get_database
from talentvoting.common.acts import parse_act

app = Flask(__name__)


def __is_vote_in_budget(transaction, user_id, round_id, act_number):
    """
    Get the voting history for the round if user has remaining votes in their budget
    and has not voted for this act.
    In a transaction, insert a new Votebudget if no Votebudget exists.
    Returns: Array of string if a Vote can be cast for this act, False otherwise
    """

    result_rows = transaction.execute_sql(
        "SELECT Total_votes_cast, voted_acts from Votebudget "+
        "WHERE Round_id = {} AND Userid = '{}'".format(round_id, user_id)
    )
    result = result_rows.one_or_none()
    if result:
        prev_total = result[0]
        prev_votes = result[1]
        if DefaultPolicyEngine.is_eligible_vote(round_id, act_number, prev_votes):
            return prev_votes
        else:
            return False
    else:
        new_votes = DefaultPolicyEngine.DEFAULT_VOTE_HISTORY
        print("creating votebudget for user {} round {}".format(user_id, round_id))
        print("new_votebudget: {}" .format(str(new_votes)))
        sql= "INSERT INTO Votebudget "+\
            "(Userid, Round_id, Last_voted_at, Total_votes_cast, Voted_acts) "+\
            "VALUES('{}',{},NULL,0,ARRAY{})".format(user_id, round_id,
                                                    str(new_votes))
        row_ct = transaction.execute_update(sql)

        if row_ct != 1:
            raise ValueError("Inserted unexpected {} rows for round {} act {}".
                             format(row_ct, round_id, act_number))

        return new_votes


def __update_vote(transaction, act_number, round_id):
    "In a transaction, increment the votes for this act by 1."
    row_ct = transaction.execute_update(
        "UPDATE Votes "
        "SET Total = Total + 1 "
        "WHERE Act_number = {} ".format(act_number) +
        "AND Round_id = {}".format(round_id)
    )
    if row_ct != 1:
        raise ValueError("Updated unexpected {} rows for round {} act {}".
                         format(row_ct, round_id, act_number))

def __update_votebudget(transaction, user_id, round_id, act_number, vote_budget):
    """
    In a transaction, update the vote history to show this act as voted for.
    The vote history is 0 indexed, act numbers start at 1 so adjust the index 
    into the history array.
    """
    vote_budget[act_number-1] = 'Y'
    print("vote_budget set to: {}".format(str(vote_budget)))
    sql= "UPDATE Votebudget "+ \
    "SET voted_acts = ARRAY{}, ".format(str(vote_budget)) + \
        "Total_votes_cast = Total_votes_cast + 1, " +\
        "Last_voted_at = CURRENT_TIMESTAMP " +\
        "WHERE Round_id = {} AND Userid = '{}'".format(round_id, user_id)
    print("UPDATE '{}'".format(sql))
    row_ct = transaction.execute_update(sql)

    if row_ct != 1:
        raise ValueError("Updated unexpected {} rows for round {} user {}"
                         .format(len(row_ct), round_id, user_id))


def _apply_vote_if_allowed(transaction, user_id, round_id, act_number):
    """
    In a transaction, check the eligibility of this vote
    and update the votes and votebudget tables.
    """
    vote_budget = __is_vote_in_budget(transaction, user_id, round_id, act_number)
    if not vote_budget:
        print("vote_budget: {}".format(vote_budget))
        print("vote out of budget, user {} round {} act {}".format(user_id,
                                                                   round_id, act_number))
        return
    __update_vote(transaction, act_number, round_id)
    __update_votebudget(transaction, user_id, round_id, act_number, vote_budget)
    return


def _process_vote(message:json) -> bool:
    """
    Process a JSON message containing a vote.
    Create a transaction and update the database if the user and act
    are in the message.
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
    round, act = parse_act(message["act"])
    get_database().run_in_transaction(_apply_vote_if_allowed,
                                      user_id=message["user"], round_id=round,
                                      act_number=act)
    return True


@app.route("/", methods=["POST"])
def index():
    """
    Receive a Pub/Sub message which should contain JSON
    and issue an HTTP response.
    Process the vote if the message contains valid JSON.
    """
    message = request.data
   
    print("incoming message!")
    if message:
        print("data: {}".format(message))
    try:
        vote = json.loads(message)
    except ValueError as e:
        print("Invalid JSON received: {}".format(e))
        return ("Invalid JSON", 400)
    try:
        if _process_vote(vote):
            print("Processed vote: {}".format(vote))
        else:
            print("Invalid vote: {}".format(vote))
            return ("Invalid vote", 400)  # Invalid content error status  
    except Exception as e:
        print("error: {}".format(e))
        return ("", 500)  # Internal server error status
    return ("", 204)  # No content OK status