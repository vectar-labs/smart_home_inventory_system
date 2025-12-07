from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from flask_login import login_user, logout_user, login_required, current_user

from app.models import User
from app import db

main = Blueprint('main', __name__)

# Authentication Routes

@main.route('/signup', methods=['GET', 'POST'])
def signup():
    
    if request.method == 'POST':
        # Handle user registration logic here
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password_hash')
        
        # validattion
        
        if not all([username, email, password]):
            flash('All fields are required', 'error')
            return render_template('register.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters', 'error')
            return render_template('register.html')
        
         # Check duplicates
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'error')
            return render_template('register.html')
        
         # Create user with hashed password
        user = User(username=username, email=email)
        user.set_password(password)  # Hashes before saving
        db.session.add(user)
        db.session.commit()
        
        print(f"Registered user: {username} (ID: {user.id})")  # No password in logs
        flash('Account created successfully!', 'success')
        return redirect(url_for('main.login'))
        
    if request.method == 'GET':
        return render_template('register.html')

@main.route('/', methods=['GET', 'POST'])
def login():
    
    if current_user.is_authenticated:  # Already logged in
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password_hash')
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('main.login'))


# Dashboard Routes  
@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

# inventory Routes

@main.route('/inventory')
@login_required
def inventory():
    return render_template('inventory.html', user=current_user)

@main.route('/add_item')
@login_required
def add_item():
    return render_template('add_item.html', user=current_user)

@main.route('/edit_item')
@login_required
def edit_item():
    return render_template('edit_item.html', user=current_user)

@main.route('/delete_item')
@login_required
def delete_item():
    return "Item Deleted"

# shopping list Routes

@main.route('/shopping_list')
@login_required
def shopping_list():
    return render_template('shopping_list.html', user=current_user)


# consumption Routes

@main.route('/consumption')
@login_required
def consumption():
    return render_template('consumption_log.html', user=current_user)

@main.route('/add_consumption')
@login_required
def add_consumption():
    return render_template('add_consumption.html', user=current_user)

@main.route('/edit_consumption')
@login_required
def edit_consumption():
    return render_template('edit_consumption.html', user=current_user)