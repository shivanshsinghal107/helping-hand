import os
import json
import requests
import datetime

from flask import Flask, request, render_template, redirect
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Set up database
engine = create_engine(os.getenv("DATABASE_URI", "sqlite:///database.db"))
db = scoped_session(sessionmaker(bind=engine))

API_KEY = os.getenv("IPSTACK_API_KEY")

@app.route("/", methods = ['GET', 'POST'])
def index():
    if request.headers.getlist("X-Forwarded-For"):
       ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
       ip = request.remote_addr
    
    url = f'http://api.ipstack.com/{ip}?access_key={API_KEY}'
    r = requests.get(url)
    j = json.loads(r.text)
    city = j['city']
    print(url)
    print(ip)
    print(city)
    return j
