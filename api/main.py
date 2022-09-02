from ast import Pass
from ctypes.wintypes import ULONG
from typing import Tuple
from fastapi import FastAPI
from pydantic import BaseModel
from google.cloud import firestore
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


class UserRequest(BaseModel):
  uname: str
  passwd: str


app = FastAPI()
db = firestore.AsyncClient.from_service_account_json('./cred.json')
hasher = PasswordHasher()


@app.post("/register")
async def root(user: UserRequest):
  col = db.collection('users')
  foundUsers = col.where('username', '==', user.uname).stream()
  foundUsers = [user async for user in foundUsers]
  print(len(foundUsers))
  if len(foundUsers) == 0:
    passwd = hasher.hash(user.passwd)
    try:
      await col.add({'username': user.uname, 'password': passwd})
      return {'ok': True}
    except Exception as e:
      return {'ok': False, 'error': 'unknown error'}
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
      return {'ok': True}
    except VerifyMismatchError as e:
      return {'ok': False, 'error': 'passowrd does not match'}
    except Exception as e:
      return {'ok': False, 'error': 'unknown error'}

  return {'ok': False, 'error': 'user not found'}
