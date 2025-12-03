from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app(class_config=Config):
    app = Flask(__name__)
    app.config.from_object(class_config)
    
    with app.app_context():
        from .models import User, Category, Location, Units, GroceryItem, ConsumptionLog
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    from .routes import main
    app.register_blueprint(main)
    from . import routes

    return app