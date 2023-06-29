from datetime import datetime, timedelta

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed, ParseError

User = get_user_model()

class TokenPayload:
  def __init__(self, payload):
    self.user_identifier = payload.get('user_identifier')
    self.exp = payload.get('exp')
    self.iat = payload.get('iat')
    self.username = payload.get('username')
    self.role = payload.get('role')

def verify_jwt(token):  # From : https://medium.com/codex/django-rest-framework-custom-jwt-authentication-backend-17bbd178b4fd
  # Decode the JWT and verify its signature
  try:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
    return TokenPayload(payload)
  except jwt.exceptions.InvalidSignatureError:
    raise AuthenticationFailed('Invalid signature')
  except:
    raise ParseError()

def create_jwt(username, role):
  # Create the JWT payload
  payload = {
    'user_identifier': username,
    'exp': int((datetime.now() + timedelta(hours=settings.TOKEN_LIFETIME_HOURS)).timestamp()),
    # set the expiration time for 5 hour from now
    'iat': datetime.now().timestamp(),
    'username': username,
    'role': role,
  }
  # Encode the JWT with your secret key
  jwt_token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
  return jwt_token.decode('utf-8')

class JWTAuthentication(authentication.BaseAuthentication):
  def authenticate(self, request):
    # Extract the JWT from the Authorization header
    jwt_token = request.META.get('HTTP_AUTHORIZATION')
    if jwt_token is None:
      return None

    jwt_token = JWTAuthentication.get_the_token_from_header(jwt_token)  # clean the token

    # Decode the JWT and verify its signature
    try:
      payload = jwt.decode(jwt_token, settings.SECRET_KEY, algorithms=['HS256'])
    except jwt.exceptions.InvalidSignatureError:
      raise AuthenticationFailed('Invalid signature')
    except:
      raise ParseError()

    # Get the user from the database
    username_or_phone_number = payload.get('user_identifier')
    if username_or_phone_number is None:
        raise AuthenticationFailed('User identifier not found in JWT')

    user = User.objects.filter(username=username_or_phone_number).first()
    if user is None:
      user = User.objects.filter(phone_number=username_or_phone_number).first()
      if user is None:
        raise AuthenticationFailed('User not found')

    # Return the user and token payload
    return user, payload

  def authenticate_header(self, request):
    return 'Bearer'

  @classmethod
  def create_jwt(cls, user):
    # Create the JWT payload
    payload = {
      'user_identifier': user.username,
      'exp': int((datetime.now() + timedelta(hours=settings.JWT_CONF['TOKEN_LIFETIME_HOURS'])).timestamp()),
      # set the expiration time for 5 hour from now
      'iat': datetime.now().timestamp(),
      'username': user.username,
      'phone_number': user.phone_number
    }

    # Encode the JWT with your secret key
    jwt_token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

    return jwt_token

  @classmethod
  def get_the_token_from_header(cls, token):
    token = token.replace('Bearer', '').replace(' ', '')  # clean the token
    return token