from flask import Blueprint, render_template

main = Blueprint('main', __name__)

# Authentication Routes

@main.route('/')
def login():
    return render_template('login.html')
@main.route('/signup')
def signup():
    return render_template('register.html')


# Dashboard Routes  
@main.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# inventory Routes

@main.route('/inventory')
def inventory():
    return render_template('inventory.html')

@main.route('/add_item')
def add_item():
    return render_template('add_item.html')

@main.route('/edit_item')
def edit_item():
    return render_template('edit_item.html')

@main.route('/delete_item')
def delete_item():
    return "Item Deleted"

# shopping list Routes

@main.route('/shopping_list')
def shopping_list():
    return render_template('shopping_list.html')


# consumption Routes

@main.route('/consumption')
def consumption():
    return render_template('consumption_log.html')

@main.route('/add_consumption')
def add_consumption():
    return render_template('add_consumption.html')

@main.route('/edit_consumption')
def edit_consumption():
    return render_template('edit_consumption.html')