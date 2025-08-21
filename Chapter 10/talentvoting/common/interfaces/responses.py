from abc import abstractmethod, ABC


class FrontendError(Exception, ABC):
   def __str__(self) ->str:
      return self.__class__.__name__ + ":" + str(self.response())
   
   @abstractmethod
   def response(self) ->any:
      "Always provide a response method specific to the error subclass"
      pass


class IneligibleVote(FrontendError):
    def __init__(self, user, act):
        self.__user = user
        self.__act = act

    def response(self) ->any:
                   
     return ("error:Ineligible vote. "+
         "user:{}. act:{}".format(str(self.__user),str(self.__act)),
     403)
        

class InvalidUser(FrontendError):
    def __init__(self, user):
        self.__user = user

    def response(self) ->any:
     return ("error:Unknown user. id:{}".format(str(self.__user)),
     401)
 

class InvalidLogin(FrontendError):
    def __init__(self, id):
        self.__id = id

    def response(self) ->any:
     return ("error:Invalid or missing user. id:{}".format(self.__id),
     400)

class MalformedRequest(FrontendError):
    def __init__(self, name):
        self.__name = name

    def response(self) ->any:
     return ("error:Missing or invalid request parameters. name:{}".format(self.__name),
     400)
    

class VoteCastError(FrontendError):
    def __init__(self, act):
        self.__act = act

    def response(self) ->any:
                   
     return ("error:vote not recorded. "+
         "act:{}".format(str(self.__act)),
     500)     