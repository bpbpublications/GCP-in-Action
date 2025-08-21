from typing import List, Dict

# For now an Act is a JSON object with no stricter definition enforced
Act = Dict[str, any]

# Any number of Acts are often referenced as a group
Acts = List[Act]

# This is a helper stub to use until we define backing storage services for Acts
def example_acts() ->Acts:
    act1 = {"season": 1, "act": "S01A001", "name": "Crazy good rock", "voting_eligible": True}
    act2 = {"season": 1, "act": "S01A002", "name": "Serious Wizardry", "voting_eligible": True}
    act3 = {"season": 1, "act": "S01A004", "name": "Acrobatic comedy", "voting_eligible": False}

    acts  =  list(        
        [act1, act2, act3]
        )
    return acts