import psycopg2
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine

from .read_data import Check_data_online

app = FastAPI()

templates = Jinja2Templates(directory="templates")


@app.get('/')
def root(request: Request):
    conn_string = 'postgresql://myprojectuser:password@localhost/myproject'
    db = create_engine(conn_string)
    conn = db.connect()
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()
    sql1 = '''select * from data;'''
    cursor.execute(sql1)
    data = cursor.fetchall()
    for i in cursor.fetchall():
        print(i)
    return templates.TemplateResponse("index.html",
                                      {"request": request, "data": data})
