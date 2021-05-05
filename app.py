import os
import string
import random
import smtplib
import tweepy
import datetime

from geopy.exc import GeocoderTimedOut
from geopy.geocoders import Nominatim
from googleplaces import GooglePlaces, types, lang
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import Flask, request, render_template, redirect
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Set up database
engine = create_engine(os.getenv("DATABASE_URI", "sqlite:///database.db"))
db = scoped_session(sessionmaker(bind=engine))

# credentails
PASSWORD = os.getenv("PASSWORD")
USER = os.getenv("USER")
PASSW = os.getenv("PASSW")

# twitter credentials
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

# google maps api
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

def send_mail(email, subject, body):
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.ehlo()

    server.login('helpinghand.cov19@gmail.com', PASSWORD)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = "helpinghand.cov19@gmail.com"
    msg["To"] = email

    msg.attach(MIMEText(body, 'html'))

    server.sendmail('helpinghand.cov19@gmail.com', email, msg.as_string())
    print("HEY, EMAIL HAS BEEN SENT!")

    server.quit()

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
        return redirect(f"/results/{city}")

@app.route("/help", methods = ['GET', 'POST'])
def help():
    return render_template("get.html")

@app.route("/about", methods = ['GET', 'POST'])
def about():
    return render_template("about.html")

@app.route("/process", methods = ['GET', 'POST'])
def process():
    if request.method == 'GET':
        return render_template("get.html")
    else:
        table = request.form.get("help")
        name = request.form.get("name")
        email = request.form.get("email")
        district = request.form.get("district")
        phone = request.form.get("phone")
        req = request.form.get("req")
        bgroup = request.form.get("bgroup")
        text = request.form.get("note")
        date = str(datetime.datetime.utcnow())
        unique_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

        if table == "giveleads":
            regex1 = '^[0-9]{12}@[a-z]{3}.svnit.ac.in$'
            email1 = re.search(regex1, email)
            regex2 = '^[0-9]{12}@[a-z]{4}.svnit.ac.in$'
            email2 = re.search(regex2, email)

            if (email1 == None) and (email2 == None):
                table = "buffer"

        db.execute(f"INSERT INTO {table} (unique_id, name, district, date, requirements, bgroup, phone, email, note) VALUES (:unique_id, :name, :district, :date, :requirements, :bgroup, :phone, :email, :note)", {"unique_id": unique_id, "name": name, "district": district, "date": date, "requirements": req, "bgroup": bgroup, "phone": phone, "email": email, "note": text})
        db.commit()
        db.close()

        print(table, name, email, district, phone, req, bgroup, text, date)

        city = district.replace(" ", "-")
        return redirect(f"/posts/{table}/{city}/{unique_id}")

@app.route("/posts/<table>/<city>/<unique_id>", methods = ['GET', 'POST'])
def posts(table, city, unique_id):
    days = []
    curr = db.execute(f"SELECT * FROM {table} WHERE unique_id = :unique_id", {"unique_id": unique_id}).fetchall()[0]
    req = curr['requirements']

    auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
    auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)

    api = tweepy.API(auth)
    if "oxygen" in req.lower():
        hashtag = "#oxygen"
    elif "hospital" in req.lower():
        hashtag = "#hospitalbed"
    elif "icu" in req.lower():
        hashtag = "#icu OR #ventilator"
    else:
        hashtag = f"#{req.lower()}"

    if table == "gethelp":
        city = city.replace("-", " ")
        location = findLatLng(f"{city}, India")
        print(city)
        print(location.latitude, location.longitude)

        tweets = tweepy.Cursor(api.search, q = hashtag, lang = "en", tweet_mode = "extended", geocode=f'{location.latitude},{location.longitude},100km', result_type='recent').items(20)
        tweets_list = [tweet for tweet in tweets]

        usernames = []
        locations = []
        retweets = []
        texts = []
        urls = []
        for tweet in tweets_list:
            if tweet.user.screen_name not in usernames:
                usernames.append(tweet.user.screen_name)
                locations.append(tweet.user.location)
                retweets.append(tweet.retweet_count)
                try:
                    text = tweet.retweeted_status.full_text
                except:
                    text = tweet.full_text
                texts.append(text)
                urls.append(f"https://twitter.com/{tweet.user.screen_name}")

        google_places = GooglePlaces(GOOGLE_MAPS_API_KEY)
        query_result = google_places.nearby_search(
            lat_lng ={'lat': location.latitude, 'lng': location.longitude},
            radius = 20000,
            types =[types.TYPE_HOSPITAL])

        h = 0
        places = []
        for place in query_result.places[:15]:
            place.get_details()
            places.append({'name': place.name, 'url': place.url})
            h += 1
        print(h)

        email = curr['email']
        data = db.execute("SELECT * FROM giveleads WHERE district = :district AND requirements = :requirements", {"district": city, "requirements": req}).fetchall()
        if len(data) > 0:
            body = ""
            for d in data:
                date = datetime.date(int(d['date'][:4]), int(d['date'][5:7]), int(d['date'][8:10]))
                diff = datetime.date.today() - date
                if diff.days == 0:
                    day = "Today"
                elif diff.days == 1:
                    day = "1 day ago"
                else:
                    day = f"{diff.days} days ago"
                days.append(day)
                body += f"""\
                    <html>
                    <body>
                        <b>{req}</b> ({day})<br><br>
                        Lead given by: {d['name']}<br>
                        Location: {d['district']}<br>
                        Phone: <a href="tel:{d['phone']}">{d['phone']}</a><br>
                        Email: <a href="mailto:{d['email']}">{d['email']}</a><br><br>
                        <a href='https://helping-hand-covid-19.herokuapp.com/feedback/{curr['unique_id']}'>If you found this helpful, let us know.</a><br>
                        <a href='https://helping-hand-covid-19.herokuapp.com/unsubscribe/{curr['unique_id']}'>Got the help? Unsubscribe.</a><br>
                        <br><i>Please respond if you feel the lead provided is a spam by clicking on the below link:</i><br>
                        <a href='https://helping-hand-covid-19.herokuapp.com/report/{d['unique_id']}'>Report Spam</a>
                        <br><br><br>
                    </body>
                    </html>
                """
                # body = f"{req} ({day})\n\nLead given by: {d['name']}\nLocation: {d['district']}\nPhone: {d['phone']}\nEmail: {d['email']}"
            db.close()
            try:
                send_mail(email, "Lead Found", body)
            except:
                print("Invalid email")
            return render_template("result.html", helps = 1, table = table, places = places, data = data, days = days, length = len(usernames), usernames = usernames, locations = locations, retweets = retweets, texts = texts, urls = urls)
        else:
            db.close()
            return render_template("result.html", helps = 0, table = "", places = places, length = len(usernames), usernames = usernames, locations = locations, retweets = retweets, texts = texts, urls = urls)
    elif table == "buffer":
        data = db.execute("SELECT * FROM gethelp WHERE district = :district AND requirements = :requirements", {"district": city, "requirements": req}).fetchall()
        db.close()
        city = city.replace("-", " ")
        location = findLatLng(f"{city}, India")
        print(city)
        print(location.latitude, location.longitude)

        tweets = tweepy.Cursor(api.search, q = hashtag, lang = "en", tweet_mode = "extended", geocode=f'{location.latitude},{location.longitude},100km', result_type='recent').items(20)
        tweets_list = [tweet for tweet in tweets]

        usernames = []
        locations = []
        retweets = []
        texts = []
        urls = []
        for tweet in tweets_list:
            if tweet.user.screen_name not in usernames:
                usernames.append(tweet.user.screen_name)
                locations.append(tweet.user.location)
                retweets.append(tweet.retweet_count)
                try:
                    text = tweet.retweeted_status.full_text
                except:
                    text = tweet.full_text
                texts.append(text)
                urls.append(f"https://twitter.com/{tweet.user.screen_name}")

        if len(data) > 0:
            return render_template("result.html", helps = 1, table = table, data = data, days = days, length = len(usernames), usernames = usernames, locations = locations, retweets = retweets, texts = texts, urls = urls)
        else:
            return render_template("result.html", helps = 1, table = table, length = len(usernames), usernames = usernames, locations = locations, retweets = retweets, texts = texts, urls = urls)
    else:
        data = db.execute("SELECT * FROM gethelp WHERE district = :district AND requirements = :requirements", {"district": city, "requirements": req}).fetchall()
        city = city.replace("-", " ")
        location = findLatLng(f"{city}, India")
        print(city)
        print(location.latitude, location.longitude)

        tweets = tweepy.Cursor(api.search, q = hashtag, lang = "en", tweet_mode = "extended", geocode=f'{location.latitude},{location.longitude},100km', result_type='recent').items(20)
        tweets_list = [tweet for tweet in tweets]

        usernames = []
        locations = []
        retweets = []
        texts = []
        urls = []
        for tweet in tweets_list:
            if tweet.user.screen_name not in usernames:
                usernames.append(tweet.user.screen_name)
                locations.append(tweet.user.location)
                retweets.append(tweet.retweet_count)
                try:
                    text = tweet.retweeted_status.full_text
                except:
                    text = tweet.full_text
                texts.append(text)
                urls.append(f"https://twitter.com/{tweet.user.screen_name}")
        if len(data) > 0:
            for d in data:
                date = datetime.date(int(d['date'][:4]), int(d['date'][5:7]), int(d['date'][8:10]))
                diff = datetime.date.today() - date
                if diff.days == 0:
                    day = "Today"
                elif diff.days == 1:
                    day = "1 day ago"
                else:
                    day = f"{diff.days} days ago"
                days.append(day)
                body = f"""\
                    <html>
                    <body>
                        <b>{req}</b> ({day})<br><br>
                        Lead given by: {curr['name']}<br>
                        Location: {curr['district']}<br>
                        Phone: <a href="tel:{curr['phone']}">{curr['phone']}</a><br>
                        Email: <a href="mailto:{curr['email']}">{curr['email']}</a><br><br>
                        <a href='https://helping-hand-covid-19.herokuapp.com/feedback/{d['unique_id']}'>If you found this helpful, let us know.</a><br>
                        <a href='https://helping-hand-covid-19.herokuapp.com/unsubscribe/{d['unique_id']}'>Got the help? Unsubscribe.</a><br>
                        <br><i>Please respond if you feel the lead provided is a spam by clicking on the below link:</i><br>
                        <a href='https://helping-hand-covid-19.herokuapp.com/report/{curr['unique_id']}'>Report Spam</a>
                    </body>
                    </html>
                """
                # body = f"{req} ({day})\n\nLead given by: {curr['name']}\nLocation: {curr['district']}\nPhone: {curr['phone']}\nEmail: {curr['email']}"
                try:
                    send_mail(d['email'], "Lead Found", body)
                except:
                    print("Invalid email")
            # increase the helped count by 1
            helped = db.execute("SELECT count FROM helped").fetchall()[0]['count']
            helped += 1
            db.execute("UPDATE helped SET count = :count", {"count": helped})
            db.commit()
            db.close()
            print(f"helped count: {helped}")

            return render_template("result.html", helps = 1, table = table, data = data, days = days, length = len(usernames), usernames = usernames, locations = locations, retweets = retweets, texts = texts, urls = urls)
        else:
            db.close()
            return render_template("result.html", helps = 1, table = table, length = len(usernames), usernames = usernames, locations = locations, retweets = retweets, texts = texts, urls = urls)

@app.route("/results/<city>", methods = ['GET', 'POST'])
def hospitals(city):
    city = city.replace("-", " ")
    location = findLatLng(f"{city}, India")
    print(city)
    print(location.latitude, location.longitude)

    auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
    auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)

    api = tweepy.API(auth)
    hashtag = "#covidhelp OR #vaccination"

    tweets = tweepy.Cursor(api.search, q = hashtag, lang = "en", tweet_mode = "extended", geocode=f'{location.latitude},{location.longitude},100km', result_type='recent').items(20)
    tweets_list = [tweet for tweet in tweets]

    usernames = []
    locations = []
    retweets = []
    texts = []
    urls = []
    for tweet in tweets_list:
        if tweet.user.screen_name not in usernames:
            usernames.append(tweet.user.screen_name)
            locations.append(tweet.user.location)
            retweets.append(tweet.retweet_count)
            try:
                text = tweet.retweeted_status.full_text
            except:
                text = tweet.full_text
            texts.append(text)
            urls.append(f"https://twitter.com/{tweet.user.screen_name}")

    google_places = GooglePlaces(GOOGLE_MAPS_API_KEY)
    query_result = google_places.nearby_search(
        lat_lng ={'lat': location.latitude, 'lng': location.longitude},
        radius = 20000,
        types =[types.TYPE_HOSPITAL])

    h = 0
    places = []
    for place in query_result.places:
        place.get_details()
        places.append({'name': place.name, 'url': place.url})
        h += 1
    print(h)

    return render_template("result.html", length = len(usernames), usernames = usernames, locations = locations, retweets = retweets, texts = texts, urls = urls, table = "")

@app.route("/report/<unique_id>", methods = ['GET', 'POST'])
def report(unique_id):
    return render_template("spam.html", unique_id = unique_id, table = "giveleads")

@app.route("/unsubscribe/<unique_id>", methods = ['GET', 'POST'])
def unsubscribe(unique_id):
    return render_template("spam.html", unique_id = unique_id, table = "gethelp")

@app.route("/delete", methods = ['GET', 'POST'])
def delete():
    if request.method == 'GET':
        return redirect("/")
    else:
        table = request.form.get("table")
        unique_id = request.form.get("unique_id")
        data = db.execute(f"SELECT * FROM {table} WHERE unique_id = :unique_id", {"unique_id": unique_id}).fetchall()
        if len(data) > 0:
            db.execute(f"DELETE FROM {table} WHERE unique_id = :unique_id", {"unique_id": unique_id})
            db.commit()
            db.close()
            return "<script>alert('Record Removed'); window.location = 'https://helping-hand-covid-19.herokuapp.com/';</script>"
        else:
            db.close()
            redirect("/")

@app.route("/feedback/<unique_id>", methods = ['GET', 'POST'])
def feedback(unique_id):
    return render_template("feedback.html", unique_id = unique_id)

@app.route("/submit-feedback", methods = ['GET', 'POST'])
def submit_feedback():
    if request.method == 'GET':
        return redirect("/")
    else:
        unique_id = request.form.get("unique_id")
        feedback = request.form.get("feedback")
        data = db.execute("SELECT * FROM feedback WHERE unique_id = :unique_id", {"unique_id": unique_id}).fetchall()
        if len(data) == 0:
            db.execute("INSERT INTO feedback (unique_id, note) VALUES (:unique_id, :note)", {"unique_id": unique_id, "note": feedback})
            db.commit()
            db.close()
            return "<script>alert('Thanks for the feedback'); window.location = 'https://helping-hand-covid-19.herokuapp.com/';</script>"
        else:
            db.close()
            redirect("/")

@app.route("/leads/verify", methods = ['GET', 'POST'])
def login():
    if request.method == "GET":
        return render_template("login.html")
    else:
        user = request.form.get("username")
        passw = request.form.get("password")

        if (user == USER) and (passw == PASSW):
            data = db.execute("SELECT * FROM buffer").fetchall()
            db.close()
            if len(data) > 0:
                return render_template("verify.html", data = data)
            else:
                return render_template("verify.html")
        else:
            return "<script>alert('Wrong credentails'); window.location = window.history.back();</script>"

@app.route("/verified/<unique_id>", methods = ['GET', 'POST'])
def verified(unique_id):
    curr = db.execute(f"SELECT * FROM buffer WHERE unique_id = :unique_id", {"unique_id": unique_id}).fetchall()[0]
    name = curr['name']
    email = curr['email']
    district = curr['district']
    phone = curr['phone']
    req = curr['requirements']
    bgroup = curr['bgroup']
    text = curr['note']
    date = curr['date']
    unique_id = curr['unique_id']

    db.execute("INSERT INTO giveleads (unique_id, name, district, date, requirements, bgroup, phone, email, note) VALUES (:unique_id, :name, :district, :date, :requirements, :bgroup, :phone, :email, :note)", {"unique_id": unique_id, "name": name, "district": district, "date": date, "requirements": req, "bgroup": bgroup, "phone": phone, "email": email, "note": text})
    db.execute("DELETE FROM buffer WHERE unique_id = :unique_id", {"unique_id": unique_id})
    db.commit()

    print("verified", name, email, district, phone, req, bgroup, text, date)

    data = db.execute("SELECT * FROM gethelp WHERE district = :district AND requirements = :requirements", {"district": district, "requirements": req}).fetchall()
    if len(data) > 0:
        days = []
        for d in data:
            date = datetime.date(int(d['date'][:4]), int(d['date'][5:7]), int(d['date'][8:10]))
            diff = datetime.date.today() - date
            if diff.days == 0:
                day = "Today"
            elif diff.days == 1:
                day = "1 day ago"
            else:
                day = f"{diff.days} days ago"
            days.append(day)
            body = f"""\
                <html>
                <body>
                    <b>{req}</b> ({day})<br><br>
                    Lead given by: {curr['name']}<br>
                    Location: {curr['district']}<br>
                    Phone: <a href="tel:{curr['phone']}">{curr['phone']}</a><br>
                    Email: <a href="mailto:{curr['email']}">{curr['email']}</a><br><br>
                    <a href='https://helping-hand-covid-19.herokuapp.com/feedback/{d['unique_id']}'>If you found this helpful, let us know.</a><br>
                    <a href='https://helping-hand-covid-19.herokuapp.com/unsubscribe/{d['unique_id']}'>Got the help? Unsubscribe.</a><br>
                    <br><i>Please respond if you feel the lead provided is a spam by clicking on the below link:</i><br>
                    <a href='https://helping-hand-covid-19.herokuapp.com/report/{curr['unique_id']}'>Report Spam</a>
                </body>
                </html>
            """
            try:
                send_mail(d['email'], "Lead Found", body)
            except:
                print("Invalid email")
        # increase the helped count by 1
        helped = db.execute("SELECT count FROM helped").fetchall()[0]['count']
        helped += 1
        db.execute("UPDATE helped SET count = :count", {"count": helped})
        db.commit()
        print(f"helped count: {helped}")
    db.close()
    return "<script>alert('Lead verifed'); window.location = window.history.back();</script>"

@app.route("/spam/<unique_id>", methods = ['GET', 'POST'])
def spam(unique_id):
    db.execute("DELETE FROM buffer WHERE unique_id = :unique_id", {"unique_id": unique_id})
    db.commit()
    db.close()

    return "<script>alert('Record removed'); window.location = window.history.back();</script>"
