from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from app.forms import RegistrationForm, LoginForm, GroceryItemForm, EditGroceryItemForm, ConsumptionLogForm, EditConsumptionLogForm
from app.models import User, Location, Category, GroceryItem, Units, ConsumptionLog 
from app import db

main = Blueprint('main', __name__)

# Authentication Routes

@main.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)  # Hashes before saving
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('register.html', form=form)

@main.route('/', methods=['GET', 'POST'])
def login():
    
    if current_user.is_authenticated:  # Already logged in
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    
    if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user)
                return redirect(url_for('main.dashboard'))
            else:
                flash('Invalid email or password', 'error')
    return render_template('login.html', form=form)
    

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully, see you soon', 'success')
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
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category_id', type=int)
    location_id = request.args.get('location_id', type=int)
    sort = request.args.get('sort', 'name')

    query = GroceryItem.query.filter_by(user_id=current_user.id)

    if search:
        query = query.filter(GroceryItem.name.ilike(f"%{search}%"))

    if category_id:
        query = query.filter(GroceryItem.category_id == category_id)

    if location_id:
        query = query.filter(GroceryItem.location_id == location_id)

    if sort == 'expiry':
        query = query.order_by(GroceryItem.expiry_date.asc().nulls_last())
    elif sort == 'quantity':
        query = query.order_by(GroceryItem.quantity.desc())
    else:
        query = query.order_by(GroceryItem.name.asc())

    grocery_items = query.all()

    categories = Category.query.order_by(Category.name).all()
    locations = Location.query.order_by(Location.name).all()

    return render_template(
        'inventory.html',user=current_user,
        grocery_items=grocery_items,
        categories=categories,
        locations=locations,
        search=search,
        category_id=category_id,
        location_id=location_id,
        sort=sort,
        today=date.today(),
    )

@main.route('/add_item', methods=['GET', 'POST'])
@login_required
def add_item():
    form = GroceryItemForm()
    # Query choices dynamically inside route
    categories = [(0, 'Select Category')] + [(c.id, c.name) for c in Category.query.all()]
    locations = [(0, 'Select Location')] + [(l.id, l.name) for l in Location.query.all()]
    units = [(0, 'Select Unit')] + [(u.id, u.name) for u in Units.query.all()]

    form.category_id.choices = categories
    form.location_id.choices = locations
    form.unit_id.choices = units
    
    if form.validate_on_submit():
        # Process form data and add item to database
        
        category_id = form.category_id.data or None 
        location_id = form.location_id.data or None 
        unit_id = form.unit_id.data or None
        
        item = GroceryItem(
            name=form.name.data,
            category_id=category_id,
            quantity=form.quantity.data,
            expiry_date=form.expiry_date.data,
            purchase_date=form.purchase_date.data,
            location_id=location_id,
            unit_id=unit_id,
            barcode=form.barcode.data,
            user_id=current_user.id
        )
        db.session.add(item)
        db.session.commit()
       
        return redirect(url_for('main.inventory'))
         
   
    return render_template('add_item.html', user=current_user, form=form)

@main.route('/grocery/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    form = EditGroceryItemForm()
    item = GroceryItem.query.get_or_404(item_id)
    # Query choices dynamically inside route
    categories = [(0, 'Select Category')] + [(c.id, c.name) for c in Category.query.all()]
    locations = [(0, 'Select Location')] + [(l.id, l.name) for l in Location.query.all()]
    units = [(0, 'Select Unit')] + [(u.id, u.name) for u in Units.query.all()]
    form.category_id.choices = categories
    form.location_id.choices = locations
    form.unit_id.choices = units
    if form.validate_on_submit():
        item.name = form.name.data
        item.category_id = form.category_id.data
        item.quantity = form.quantity.data
        item.expiry_date = form.expiry_date.data
        item.purchase_date = form.purchase_date.data
        item.location_id = form.location_id.data
        item.unit_id = form.unit_id.data
        item.barcode = form.barcode.data
        db.session.commit()
      
        return redirect(url_for('main.inventory'))
    elif request.method == 'GET':
        form.name.data = item.name
        form.category_id.data = item.category_id
        form.quantity.data = item.quantity
        form.expiry_date.data = item.expiry_date
        form.purchase_date.data = item.purchase_date
        form.location_id.data = item.location_id
        form.unit_id.data = item.unit_id
        form.barcode.data = item.barcode
        
    return render_template('edit_item.html', form=form, item=item, user=current_user)

@main.route('/grocery/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_grocery(item_id):
    item = GroceryItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    
    return redirect(url_for('main.inventory'))

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