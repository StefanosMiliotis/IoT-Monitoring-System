from fastapi import FastAPI
from psydantic import BaseModel
import os 
import psycopg2 

app = FastAPI()


# @app.get("/")
# def read_root():
#     return {""}


# @app.get("/items/{item_id}")
# def read_item(item_id: int, q: str | None = None):
#     return {"item_id": item_id, "q": q}