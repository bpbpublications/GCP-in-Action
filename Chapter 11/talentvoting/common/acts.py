from typing import List, Dict

# For now an Act is a JSON object with no stricter definition enforced
Act = Dict[str, any]

# Any number of Acts are often referenced as a group
Acts = List[Act]

def parse_act(act:str)->tuple[int,int]:
    "Extract round ID and act number from act string."
    round = int(act[1:3])
    act = int(act[4:])
    return (round,act)

# This is a helper stub to use until we define backing storage services for Acts
def example_acts() ->Acts:
    "Return an array of acts for an example round."
    act1 = {"season": 1, "act": "S01A001", "name": "Crazy good rock", "voting_eligible": True}
    act2 = {"season": 1, "act": "S01A002", "name": "Serious Wizardry", "voting_eligible": True}
    act3 = {"season": 1, "act": "S01A003", "name": "Inspiring singer", "voting_eligible": True}
    act4 = {"season": 1, "act": "S01A004", "name": "Acrobatic comedy", "voting_eligible": True}
    act5 = {"season": 1, "act": "S01A005", "name": "Funny funny dogs", "voting_eligible": True}
    act6 = {"season": 1, "act": "S01A006", "name": "Mesmerizing Millie", "voting_eligible": True}
    act7 = {"season": 1, "act": "S01A007", "name": "Looney daredevils", "voting_eligible": True}
    act8 = {"season": 1, "act": "S01A008", "name": "All child chorus", "voting_eligible": True}
    act9 = {"season": 1, "act": "S01A009", "name": "Front street duet", "voting_eligible": True}
    act10 = {"season": 1, "act": "S01A010", "name": "First avenue boys", "voting_eligible": True}
    act11 = {"season": 1, "act": "S01A011", "name": "Dueling bananas", "voting_eligible": True}
    act12 = {"season": 1, "act": "S01A012", "name": "Knife throwing chimps", "voting_eligible": True}

    acts  =  list(        
        [act1, act2, act3, act4, act5, act6, act7, act8, act9, act10, act11, act12]
        )
    return acts