from ctypes.wintypes import ULONG
from typing import Tuple
from fastapi import FastAPI
from pydantic import BaseModel
from google.cloud import firestore


class UserRequest(BaseModel):
  uname: str
  passwd: str


app = FastAPI()
db = firestore.AsyncClient.from_service_account_json(
    './bamboo-drive-305101-c24f458db77e.json')


@app.post("/register")
async def root(user: UserRequest):
  col = db.collection('users')
  foundUsers = col.where('username', '==', user.uname).stream()
  foundUsers = [user async for user in foundUsers]
  print(len(foundUsers))
  if len(foundUsers) == 0:
    doc: firestore.DocumentReference = None
    await col.add({'username': user.uname, 'password': user.passwd})
    return {'ok': True}
  else:
    return {'ok': False, 'msg': 'user already exist'}

@app.post("/login")
async def login():
  col = db.collection('users')
  return {}