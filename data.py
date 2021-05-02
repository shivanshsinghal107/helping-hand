import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Set up database
engine = create_engine(os.getenv("DATABASE_URL", "sqlite:///database.db"))
db = scoped_session(sessionmaker(bind=engine))

def make_tables():
    db.execute('''CREATE TABLE IF NOT EXISTS gethelp (id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(255) NOT NULL,
                  state VARCHAR(64) NOT NULL, district VARCHAR(100) NOT NULL, date VARCHAR(30), requirements text,
                  bgroup VARCHAR(5), phone VARCHAR(15), email VARCHAR(100), note text)''')
    db.execute('''CREATE TABLE IF NOT EXISTS giveleads (id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(255) NOT NULL,
                  state VARCHAR(64) NOT NULL, district VARCHAR(100) NOT NULL, date VARCHAR(30), requirements text,
                  bgroup VARCHAR(5), phone VARCHAR(15), email VARCHAR(100), note text)''')
    db.commit()
    db.close()

if __name__ == "__main__":
    make_tables()