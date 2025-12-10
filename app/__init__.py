from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
from flask import session

# Initialize extensions FIRST (before any model imports)
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.refresh_view = 'main.login'
    login_manager.needs_refresh_message = "Session timed out, please log in again"
    login_manager.needs_refresh_message_category = "info"
    login_manager.login_message = 'Session timed out, please log in again'
    migrate.init_app(app, db)
    
    with app.app_context():
        db.create_all()
        from app.models import User
        
        # Register user_loader after User import
        @login_manager.user_loader
        def load_user(user_id):
            return User.load_user(user_id)
        
        
      
       
      
    
    # Register blueprints LAST
    from .routes import main
    app.register_blueprint(main)
    from . import routes
    
    @app.before_request
    def make_session_permanent():
        
        session.permanent = True
        session.modified = True
        app.permanent_session_lifetime = app.config['PERMANENT_SESSION_LIFETIME']
    
    return app


    