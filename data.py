import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Set up database
engine = create_engine(os.getenv("DATABASE_URI", "sqlite:///database.db"))
db = scoped_session(sessionmaker(bind=engine))

def make_tables():
    db.execute('''CREATE TABLE IF NOT EXISTS gethelp (id SERIAL PRIMARY KEY, unique_id CHAR(8) NOT NULL,
                  name VARCHAR(255) NOT NULL, district VARCHAR(100) NOT NULL, date VARCHAR(30), requirements VARCHAR(255),
                  bgroup VARCHAR(5), phone VARCHAR(15), email VARCHAR(100), note text)''')
    db.execute('''CREATE TABLE IF NOT EXISTS giveleads (id SERIAL PRIMARY KEY, unique_id CHAR(8) NOT NULL,
                  name VARCHAR(255) NOT NULL, district VARCHAR(100) NOT NULL, date VARCHAR(30), requirements VARCHAR(255),
                  bgroup VARCHAR(5), phone VARCHAR(15), email VARCHAR(100), note text)''')
    db.execute('''CREATE TABLE IF NOT EXISTS feedback (id SERIAL PRIMARY KEY, unique_id CHAR(8) NOT NULL,
                  note text NOT NULL)''')
    db.execute('''CREATE TABLE IF NOT EXISTS helped (count INTEGER)''')
    db.execute("INSERT INTO helped (count) VALUES (:count)", {"count": 0})
    db.commit()
    db.close()

if __name__ == "__main__":
    make_tables()
