from abc import ABC, abstractmethod
from talentvoting.common.acts import Act, Acts

class VoteIngester(ABC):
    def __init__(self):
        pass
    
    @abstractmethod
    def _getActs() ->Acts:
        pass

    @abstractmethod
    def cast(self, user, act:Act) ->any:
        pass