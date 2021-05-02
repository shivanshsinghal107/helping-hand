import os
import tweepy
import datetime

from geopy.exc import GeocoderTimedOut
from geopy.geocoders import Nominatim
from googleplaces import GooglePlaces, types, lang

from flask import Flask, request, render_template, redirect
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Set up database
engine = create_engine(os.getenv("DATABASE_URI", "sqlite:///database.db"))
db = scoped_session(sessionmaker(bind=engine))

def findLatLng(city):
    try:
        geolocator = Nominatim(user_agent="app")
        return geolocator.geocode(city)
    except GeocoderTimedOut:
        return findLatLng(city)

@app.route("/", methods = ['GET', 'POST'])
def home():
    if request.method == 'GET':
        return render_template("home.html")
    else:
        district = request.form.get("district")
        city = district.replace(" ", "-")
        print(city)
        table = "help"
        return redirect(f"/posts/{table}/{city}")

@app.route("/help", methods = ['GET', 'POST'])
def help():
    return render_template("get.html")

@app.route("/process", methods = ['GET', 'POST'])
def process():
    if request.method == 'GET':
        return render_template("get.html")
    else:
        table = request.form.get("help")
        name = request.form.get("name")
        email = request.form.get("email")
        state = request.form.get("state")
        district = request.form.get("district")
        phone = request.form.get("phone")
        req = request.form.get("req")
        bgroup = request.form.get("bgroup")
        text = request.form.get("note")
        date = str(datetime.datetime.utcnow())

        db.execute(f"INSERT INTO {table} (name, state, district, date, requirements, bgroup, phone, email, note) VALUES (:name, :state, :district, :date, :requirements, :bgroup, :phone, :email, :note)", {"name": name, "state": state, "district": district, "date": date, "requirements": req, "bgroup": bgroup, "phone": phone, "email": email, "note": text})
        db.commit()
        db.close()

        print(table, name, email, state, district, phone, req, bgroup, text, date)

        city = district.replace(" ", "-")
        return redirect(f"/posts/{table}/{city}")

@app.route("/posts/<table>/<city>", methods = ['GET', 'POST'])
def tweets(table, city):
    city = city.replace("-", " ")
    location = findLatLng(f"{city}, India")
    print(city)
    print(location.latitude, location.longitude)
    if table == "gethelp":
        data = db.execute("SELECT * FROM giveleads WHERE district = :district", {"district": city}).fetchall()
        db.close()
    elif table == "giveleads":
        data = db.execute("SELECT * FROM gethelp WHERE district = :district", {"district": city}).fetchall()
        db.close()

    auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)

    api = tweepy.API(auth)
    hashtag = "#VaccineShortage"

    tweets = tweepy.Cursor(api.search, q = hashtag, lang = "en", tweet_mode = "extended").items(20)
    tweets_list = [tweet for tweet in tweets]

    tweet_text = "<h2>Tweets</h2>"
    for tweet in tweets_list[:10]:
        tweet_text += f"username: {tweet.user.screen_name}<br>"
        tweet_text += f"location: {tweet.user.location}<br>"
        tweet_text += f"retweets: {tweet.retweet_count}<br>"
        try:
            text = tweet.retweeted_status.full_text
        except:
            text = tweet.full_text
        tweet_text += f"text: {text}<br>"
        hashtags = [hashtag['text'] for hashtag in tweet.entities['hashtags']]
        tweet_text += f"hashtags: {hashtags}<br><br><br>"

    google_places = GooglePlaces(GOOGLE_MAPS_API_KEY)
    query_result = google_places.nearby_search(
        lat_lng ={'lat': location.latitude, 'lng': location.longitude},
        radius = 10000,
        types =[types.TYPE_HOSPITAL])

    hospitals = "<h2>Hospitals</h2>"
    h = 0
    for place in query_result.places:
        h += 1
        hospitals += f"{place.name} ({place.geo_location['lat']}, {place.geo_location['lng']})<br>"
    print(h)
    return (hospitals + tweet_text)
