import os
from datetime import timedelta

from flask import app
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "your-secret-key"
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=40)
    # SQLALCHEMY_DATABASE_URI = (
    #     os.environ.get("DATABASE_URL") or
    #     "postgresql://postgres:kitindi@localhost/grocery_db"
    # ).replace('postgres://', 'postgresql://', 1) # for compatibility
    
    database_url = os.environ.get("DATABASE_URL")
    
    if database_url:
        SQLALCHEMY_DATABASE_URI = database_url.replace('postgres://', 'postgresql://', 1)
    else:
        SQLALCHEMY_DATABASE_URI = "postgresql://postgres:kitindi@localhost/grocery_db"
        
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
#    postgresql://food_inventory_71zh_user:eT0cKqgTLybgwU2ELxp4Uxa62C8Bnb6j@dpg-d501aomuk2gs739nfgj0-a.oregon-postgres.render.com/food_inventory_71zh
    