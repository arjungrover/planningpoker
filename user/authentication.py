from rest_framework.authentication import TokenAuthentication
from user.models import Token

class UserAuthentication(TokenAuthentication):
   """
    This class will be inheriting from django inbuilt TokenAuthentication and is just telling to use our own custom Token model s 
   """
   model = Token
