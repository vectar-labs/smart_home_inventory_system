from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app(class_config=Config):
    app = Flask(__name__)
    app.config.from_object(class_config)
    
    with app.app_context():
        from .models import User, Category, Location, Units, GroceryItem, ConsumptionLog
    
    db.init_app(app)
    from .models import User
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'  # Redirect unauth to login
    login_manager.login_message = 'Login required'
    migrate.init_app(app, db)
    
    
    @login_manager.user_loader  
    def load_user(user_id):
        return User.load_user(user_id)
    
    from .routes import main
    app.register_blueprint(main)
    from . import routes

    return app