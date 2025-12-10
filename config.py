import os
from datetime import timedelta
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "your-secret-key"
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=40)
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL") or
        "postgresql://postgres:kitindi@localhost/grocery_db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False