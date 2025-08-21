from talentvoting.common.acts import Act, Acts, example_acts, parse_act
from typing import List


class VotingPolicyEngine(object):
    "This is meant to be used through its provided instance (see bottom of file)."
    MAX_VOTES_PER_ROUND = 6

    DEFAULT_VOTE_HISTORY = ['N','N','N','N','N','N','N','N','N','N','N','N']

    def __init__(self):
        self._acts = example_acts()

    def get_all_acts(self) ->Acts:
        "Return all current acts as retrieved."
        return self._acts
    
    def get_current_round_id(self)->int:
        "Parse out the round_id from the first act in the current round."
        first_act = self._acts[0]["act"]
        return parse_act(first_act)[0]
    
    @staticmethod
    def is_eligible_vote(round_id:int, act_number:int,
                        prev_votes:List[str]) ->bool:
        """"
        Determine if this vote is within the vote budget.
        The vote history is 0 indexed, act numbers start at 1 so adjust the index 
        into the history array.
        """

        if not round_id or not act_number or not prev_votes:
            return False
        prev_total = prev_votes.count('Y')
        if prev_votes[act_number-1] == 'Y':
            return False
        if prev_total >= DefaultPolicyEngine.MAX_VOTES_PER_ROUND:
            return False
        return True
    

# Provide a singleton for clients to use
DefaultPolicyEngine = VotingPolicyEngine()