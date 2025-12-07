from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), nullable=False, unique=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="member")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    grocery_items = db.relationship('GroceryItem', backref='owner', lazy=True)
    
    
    @staticmethod
    def load_user(user_id):
        # Required by Flask-Login
        return User.query.get(int(user_id))
    
    
    def set_password(self, password):
    #    Hash and store password securely
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify plaintext password against stored hash"""
        return check_password_hash(self.password_hash, password)
    
    
    

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class Units(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)

class GroceryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    quantity = db.Column(db.Float, nullable=False)
    expiry_date = db.Column(db.Date, nullable=True)
    purchase_date = db.Column(db.Date, nullable=True)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)
    barcode = db.Column(db.String(64), nullable=True)
    photo_url = db.Column(db.String(200), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class ConsumptionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    grocery_item_id = db.Column(db.Integer, db.ForeignKey('grocery_item.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    qty_used = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
