from datetime import date, timedelta,datetime
from io import BytesIO
import pandas as pd
from flask import send_file
from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy import or_
from werkzeug.security import generate_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from app.forms import RegistrationForm, LoginForm, GroceryItemForm, EditGroceryItemForm, ConsumptionLogForm, EditConsumptionLogForm, ShoppingListItemForm
from app.models import User, Location, Category, GroceryItem, Units, ConsumptionLog, ShoppingListItem
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
                login_user(user, remember=False)
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
    today = date.today()
    limit = today + timedelta(days=3)
    
    expiring_soon_items =( GroceryItem.query.filter_by(user_id=current_user.id).filter(GroceryItem.expiry_date != None).filter(GroceryItem.expiry_date >= today).filter(GroceryItem.expiry_date <= limit).all())
    expiring_soon_count = (
    GroceryItem.query
    .filter_by(user_id=current_user.id)
    .filter(GroceryItem.expiry_date != None)
    .filter(GroceryItem.expiry_date >= today)
    .filter(GroceryItem.expiry_date <= limit)
    .count()
)
    expired_items_count = GroceryItem.query.filter_by(user_id=current_user.id).filter(GroceryItem.expiry_date != None).filter(GroceryItem.expiry_date < today).count()
    
    user_item_count = GroceryItem.query.filter_by(user_id=current_user.id).count()
    
    low_stock_items = GroceryItem.query.filter_by(user_id=current_user.id).filter(GroceryItem.quantity <= 4).all()
    low_stock_count = GroceryItem.query.filter_by(user_id=current_user.id).filter(GroceryItem.quantity <= 4).count()
    return render_template('dashboard.html', user=current_user, total_items=user_item_count, expiring_soon_count=expiring_soon_count, low_stock_count=low_stock_count, expiring_soon_items=expiring_soon_items, expired_items_count=expired_items_count, low_stock_items=low_stock_items)

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


# consumption Routes

@main.route('/consumption')
@login_required
def consumption():
    search = request.args.get('q', '', type=str)              # text input
    category_id = request.args.get('category_id', type=int)   # select: name="category_id"
    period = request.args.get('period', '', type=str)         # select: name="period"
    page = request.args.get('page', 1, type=int)

    # load categories from the Category table
    categories = Category.query.order_by(Category.name.asc()).all()  # adjust field name if needed[web:49][web:51]

    # base query
    query = ConsumptionLog.query.filter_by(user_id=current_user.id)

    # search filter by item name or user name
    if search:
        like_value = f"%{search}%"
        query = query.filter(
            or_(
                ConsumptionLog.grocery_item.has(GroceryItem.name.ilike(like_value)),
                ConsumptionLog.user.has(User.username.ilike(like_value))
            )
        )

    # category filter (by id FK)
    if category_id:
        query = query.filter(
            ConsumptionLog.grocery_item.has(GroceryItem.category_id == category_id)
        )

    # period filter
    if period:
        today = datetime.utcnow().date()
        if period == 'today':
            start = today
        elif period == 'last7':
            start = today - timedelta(days=6)
        elif period == 'last30':
            start = today - timedelta(days=29)
        else:
            start = None

        if start:
            query = query.filter(
                ConsumptionLog.date >= start,
                ConsumptionLog.date <= today)

    query = query.order_by(ConsumptionLog.date.desc())
    pagination = query.paginate(page=page, per_page=20, error_out=False)
    logs = pagination.items
    
    query = query.order_by(ConsumptionLog.date.desc())

    total_logs_count = query.count()
    
    # weekly count 
    
    today = datetime.utcnow().date()
    week_start = today - timedelta(days=6)

    weekly_logs_count = ConsumptionLog.query.filter_by(user_id=current_user.id).filter(
    ConsumptionLog.date >= week_start,
    ConsumptionLog.date <= today).count()

    return render_template(
        'consumption_log.html',
        logs_count = total_logs_count,
        logs=logs,
        weekly_logs_count=weekly_logs_count,
        pagination=pagination,
        search=search,
        category_id=category_id,
        period=period,
        categories=categories
    )   
    
    
    
@main.route('/add_consumption', methods=['GET', 'POST'])
@login_required
def add_consumption():
    
    form = ConsumptionLogForm()
    # Set choices on every request
    form.grocery_item_id.choices = [(0, 'Select Item')] + [
        (i.id, i.name) for i in GroceryItem.query.filter_by(user_id=current_user.id).all()
    ]
    
    if form.validate_on_submit():
        grocery_item_id = form.grocery_item_id.data or None
        
        log = ConsumptionLog(
            grocery_item_id=grocery_item_id,
            date=form.date.data,
            qty_used=form.qty_used.data,
            user_id=current_user.id,
        )
        # Update grocery item quantity
        grocery_item = GroceryItem.query.filter_by(id=grocery_item_id, user_id=current_user.id).first()
        if grocery_item:
            grocery_item.quantity -= form.qty_used.data
            if grocery_item.quantity < 0:
                grocery_item.quantity = 0  # Prevent negative stock
        db.session.add(log)
        db.session.commit()
        
        return redirect(url_for('main.consumption'))
    
    return render_template('add_consumption.html', user=current_user, form=form)

@main.route('/edit_consumption', methods=['GET', 'POST'])
@login_required
def edit_consumption(log_id):
    form = EditConsumptionLogForm()
    log = ConsumptionLog.query.get_or_404(log_id)
    # Set choices on every request
    form.grocery_item_id.choices = [(0, 'Select Item')] + [
        (i.id, i.name) for i in GroceryItem.query.filter_by(user_id=current_user.id).all()
    ]
    if form.validate_on_submit():
        previous_qty_used = log.qty_used
        log.grocery_item_id = form.grocery_item_id.data
        log.date = form.date.data
        log.qty_used = form.qty_used.data
        
        # Update grocery item quantity based on change in qty_used
        grocery_item = GroceryItem.query.filter_by(id=log.grocery_item_id, user_id=current_user.id).first()
        if grocery_item:
            qty_difference = form.qty_used.data - previous_qty_used
            grocery_item.quantity -= qty_difference
            if grocery_item.quantity < 0:
                grocery_item.quantity = 0  # Prevent negative stock
        
        db.session.commit()
        flash('Consumption log updated successfully', 'success')
        return redirect(url_for('main.consumption'))
    elif request.method == 'GET':
        form.grocery_item_id.data = log.grocery_item_id
        form.date.data = log.date
        form.qty_used.data = log.qty_used
        
    return render_template('edit_consumption.html', user=current_user, form=form, log=log)


# download consumption log as csv
@main.route('/consumption/download', methods=['GET'])
@login_required
def download_consumption_excel():
    # Get all logs for current user, optionally join grocery item names
    logs = (ConsumptionLog.query
            .filter_by(user_id=current_user.id)
            .order_by(ConsumptionLog.date.desc())
            .all())

    # Build rows for DataFrame
    data = []
    for log in logs:
        # If you defined a relationship: ConsumptionLog.grocery_item
        item_name = log.grocery_item.name if hasattr(log, 'grocery_item') and log.grocery_item else ''
        username = log.user.username if log.user else ''
        data.append({
            'Date': log.date,
            'Item': item_name,
            'Quantity Used': log.qty_used,
            'User': username,
        })

    df = pd.DataFrame(data)

    # Create Excel in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Consumption')

    output.seek(0)

    filename = f"consumption_{current_user.username}_{date.today().isoformat()}.xlsx"

    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    
    
# shopping list Routes
@main.route('/shopping_list', methods=['GET', 'POST'])
@login_required
def shopping_list():
    form = ShoppingListItemForm()

    # Set choices on every request
    form.category_id.choices = [(0, 'Select Category')] + [
        (c.id, c.name) for c in Category.query.all()
    ]
    form.unit_id.choices = [(0, 'Select Unit')] + [
        (u.id, u.name) for u in Units.query.all()
    ]
    form.grocery_item_id.choices = [(0, 'Select Item')] + [
        (i.id, i.name) for i in GroceryItem.query.filter_by(user_id=current_user.id).filter(GroceryItem.quantity <=4).all()
    ]

    if form.validate_on_submit():
        category_id = form.category_id.data or None
        unit_id = form.unit_id.data or None
        grocery_item_id = form.grocery_item_id.data or None
        
        # check if the item already exists in the shopping list for the user
        existing_item = ShoppingListItem.query.filter_by(
            grocery_item_id=grocery_item_id,
            user_id=current_user.id
        ).first()
        if existing_item:
            flash('Item already exists in shopping list', 'error')
            return redirect(url_for('main.shopping_list'))
        

        item = ShoppingListItem(
            grocery_item_id=grocery_item_id,
            quantity=form.quantity.data,
            category_id=category_id,
            unit_id=unit_id,
            purchased=form.purchased.data,
            user_id=current_user.id,
        )
        db.session.add(item)
        db.session.commit()
        flash('Item added to shopping list', 'success')
        return redirect(url_for('main.shopping_list'))

    items = ShoppingListItem.query.filter_by(user_id=current_user.id).all()
    return render_template('shopping_list.html', form=form, items=items, user=current_user)



@main.route('/shopping_list_item/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_shopping_list_item(item_id):
    shopping_item = ShoppingListItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    grocery_item = GroceryItem.query.filter_by(id=shopping_item.grocery_item_id, user_id=current_user.id).first()
    
    if grocery_item:
        grocery_item.quantity += shopping_item.quantity  # Restock the grocery item
        
    db.session.delete(shopping_item)
    db.session.commit()
    
    return redirect(url_for('main.shopping_list'))
