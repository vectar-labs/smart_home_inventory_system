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