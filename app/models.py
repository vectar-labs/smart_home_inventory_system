from . import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(50), default="member")
    grocery_items = db.relationship('GroceryItem', backref='owner', lazy=True)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class GroceryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    expiry_date = db.Column(db.Date, nullable=True)
    purchase_date = db.Column(db.Date, nullable=True)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=True)
    barcode = db.Column(db.String(64), nullable=True)
    photo_url = db.Column(db.String(200), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class ConsumptionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    grocery_item_id = db.Column(db.Integer, db.ForeignKey('grocery_item.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    qty_used = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
