from talentvoting.common.acts import Act, Acts, example_acts

class VotingPolicyEngine(object):
    def __init__(self):
        self._acts = example_acts()

    def get_all_acts(self) ->Acts:
        return self._acts
    
    def is_eligible_vote(self, user, act:Act) ->bool:
        if user and act:
            return True
        else:
            return False