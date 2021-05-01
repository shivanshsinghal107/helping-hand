import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Set up database
engine = create_engine(os.getenv("DATABASE_URL", "sqlite:///database.db"))
db = scoped_session(sessionmaker(bind=engine))

def make_tables():
    db.execute('''CREATE TABLE IF NOT EXISTS givehelp (username VARCHAR(16) NOT NULL, password VARCHAR(64) NOT NULL, join_date text,
                PRIMARY KEY(username))''')
    db.execute('''CREATE TABLE IF NOT EXISTS seekhelp (mail VARCHAR(64) NOT NULL, username VARCHAR(16) NOT NULL, FOREIGN KEY(username)
                REFERENCES users(username) ON DELETE CASCADE ON UPDATE CASCADE, PRIMARY KEY(mail, username), UNIQUE(mail, username))''')
    db.commit()
    db.close()

if __name__ == "main":
    make_tables()