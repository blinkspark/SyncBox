from ast import Pass
from ctypes.wintypes import ULONG
from enum import Flag
from typing import Tuple
from fastapi import FastAPI
from pydantic import BaseModel
from google.cloud import firestore
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import jwt, secrets
from datetime import datetime, timedelta


class UserRequest(BaseModel):
  uname: str
  passwd: str


class VerifyRequest(BaseModel):
  token: str


app = FastAPI()
db = firestore.AsyncClient.from_service_account_json('./cred.json')
hasher = PasswordHasher()


@app.post("/register")
async def root(user: UserRequest):
  col = db.collection('users')
  foundUsers = col.where('username', '==', user.uname).stream()
  foundUsers = [user async for user in foundUsers]
  if len(foundUsers) == 0:
    passwd = hasher.hash(user.passwd)
    try:
      key = secrets.token_hex(16)
      token = jwt.encode({'exp': datetime.utcnow() + timedelta(days=14)},
                         headers={'uname': user.uname},
                         key=key)
      await col.add({'username': user.uname, 'password': passwd, 'key': key})
      return {'ok': True, 'token': token}
    except Exception as e:
      return {'ok': False, 'error': f'unknown error {e}'}
  else:
    return {'ok': False, 'error': 'user already exist'}


@app.post("/login")
async def login(user: UserRequest):
  col = db.collection('users')
  foundUsers = col.where('username', '==', user.uname).stream()
  async for foundUser in foundUsers:
    foundUser = foundUser.to_dict()
    try:
      hasher.verify(foundUser['password'], user.passwd)
      token = jwt.encode({'exp': datetime.utcnow() + timedelta(days=14)},
                         headers={'uname': foundUser['username']},
                         key=foundUser['key'])
      return {'ok': True, 'token': token}
    except VerifyMismatchError as e:
      return {'ok': False, 'error': 'passowrd does not match'}
    except Exception as e:
      return {'ok': False, 'error': f'unknown error {e}'}

  return {'ok': False, 'error': 'user not found'}


@app.post("/verify")
async def verify(req: VerifyRequest):
  header = jwt.get_unverified_header(req.token)
  col = db.collection('users')
  uname = header['uname']
  async for user in col.where('username', '==', uname).stream():
    user = user.to_dict()
    key = user['key']
    try:
      _ = jwt.decode(req.token, key=key, algorithms=['HS256'])
      return {'ok': True}
    except Exception as e:
      return {'ok': False, 'error': f'unknown error {e}'}
    finally:
      break
  return {'ok': False, 'error': 'unknown error'}
