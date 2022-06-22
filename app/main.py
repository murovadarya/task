import psycopg2
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine

from .read_data import Check_data_online

app = FastAPI()

templates = Jinja2Templates(directory="templates")


@app.get('/')
def root(request: Request):
    online_checker = Check_data_online()
    
