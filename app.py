import os
import json
import requests
import datetime

from flask import Flask, request, render_template, redirect
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL", "sqlite:///database.db"))
db = scoped_session(sessionmaker(bind=engine))

API_KEY = os.getenv("IPSTACK_API_KEY")

@app.route("/", methods = ['GET', 'POST'])
def index():
    url = f'http://api.ipstack.com/{request.remote_addr}?access_key={API_KEY}'
    r = requests.get(url)
    j = json.loads(r.text)
    city = j['city']
    print(url)
    print(API_KEY)
    print(city)
    return j
