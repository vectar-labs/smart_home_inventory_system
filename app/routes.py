from datetime import date, timedelta,datetime
from io import BytesIO
import os
import uuid
import pandas as pd
from flask import current_app, send_file
from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy import or_, func
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from flask_login import login_user, logout_user, login_required, current_user
from app.forms import ChangePasswordForm, RegistrationForm, LoginForm, GroceryItemForm, EditGroceryItemForm, ConsumptionLogForm, EditConsumptionLogForm, ShoppingListItemForm, ProfileForm, CategoryForm, LocationForm, UnitsForm
from app.models import User, Location, Category, GroceryItem, Units, ConsumptionLog, ShoppingListItem,FoodWasted, Profile
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
    
    
    # save the item into FoodWaste Model
    wasted_food_item = FoodWasted(
        item_name= item.name,
         quantity= item.quantity,
         expiry_date= item.expiry_date,
         user_id=current_user.id
    )
    
    db.session.add(wasted_food_item)
       
    db.session.delete(item)
    db.session.commit()
    
    return redirect(url_for('main.inventory'))


# consumption Routes

@main.route('/consumption')
@login_required
def consumption():
    search = request.args.get('q', '', type=str)              # text input
    item_category = request.args.get('item_category', '', type=str)              # text input
    # category_id = request.args.get('category_id', type=int)   # select: name="category_id"
    period = request.args.get('period', '', type=str)         # select: name="period"
    page = request.args.get('page', 1, type=int)

    # load categories from the Category table
    categories = Category.query.order_by(Category.name.asc()).all()  

    # base query
    query = ConsumptionLog.query.filter_by(user_id=current_user.id)

    # search filter by item name or user name
    if search:
        like_value = f"%{search}%"
        query = query.filter(
            or_(
                ConsumptionLog.item_name.ilike(like_value),
                ConsumptionLog.user.has(User.username.ilike(like_value))
            )
        )

    # category filter (by id FK)
    # if category_id:
    #     query = query.filter(
    #         ConsumptionLog.grocery_item.has(GroceryItem.category_id == category_id)
    #     )
    if item_category:
        query = query.filter(ConsumptionLog.item_category == item_category)
   

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
        # category_id=category_id,
        period=period,
        categories=categories
    )   
    
    
    
@main.route('/add_consumption', methods=['GET', 'POST'])
@login_required
def add_consumption():
    today = date.today()
    
    form = ConsumptionLogForm()
    # Set choices on every request
    form.grocery_item_id.choices = [(0, 'Select Item')] + [
        (i.id, i.name) for i in GroceryItem.query.filter_by(user_id=current_user.id).filter(GroceryItem.expiry_date >= today).all()
    ]
    
    if form.validate_on_submit():
        grocery_item_id = form.grocery_item_id.data or None
        
        grocery_item = GroceryItem.query.filter_by(id=grocery_item_id, user_id=current_user.id).first()
        
        log = ConsumptionLog(
            grocery_item_id=grocery_item_id,
            item_name = grocery_item.name,
            item_category = grocery_item.category.name,
            date=form.date.data,
            qty_used=form.qty_used.data,
            user_id=current_user.id,
        )
        # Update grocery item quantity
        grocery_item = GroceryItem.query.filter_by(id=grocery_item_id, user_id=current_user.id).filter(GroceryItem.expiry_date >= today).first()
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

@main.route('/delete_consumption/<int:log_id>', methods=['POST'])
@login_required
def delete_consumption(log_id):
    log = ConsumptionLog.query.filter_by(id=log_id, user_id=current_user.id).first_or_404()
    
    # Restore grocery item quantity
    grocery_item = GroceryItem.query.filter_by(id=log.grocery_item_id, user_id=current_user.id).first()
    if grocery_item:
        grocery_item.quantity += log.qty_used
    
    db.session.delete(log)
    db.session.commit()
    
    flash('Consumption log deleted successfully', 'success')
    return redirect(url_for('main.consumption'))


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
        item_name = log.item_name
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


# Analytics Routes

@main.route('/analytics')
@login_required
def analytics():
    today = date.today()
    limit = today + timedelta(days=3)
    
    

    total_quantity = (
    db.session.query(func.sum(GroceryItem.quantity))
    .filter_by(user_id=current_user.id)
    .scalar()) or 0

# handle None when there are no rows
    total_quantity = int(total_quantity)

    # expired_items_count = GroceryItem.query.filter_by(user_id=current_user.id).filter(GroceryItem.expiry_date != None).filter(GroceryItem.expiry_date < today).count()
    total_wasted_food  = (
    db.session.query(func.sum( FoodWasted.quantity))
    .filter_by(user_id=current_user.id).scalar()) or 0
    
    total_wasted_food = int(total_wasted_food)
    
    # items_consumed_count = ConsumptionLog.query.filter_by(user_id=current_user.id).count()
    total_consummed_quantity = (
    db.session.query(func.sum(ConsumptionLog.qty_used))
    .filter_by(user_id=current_user.id)
    .scalar()) or 0
    
    total_consummed_quantity = int(total_consummed_quantity)

    items_tracked = total_quantity - total_wasted_food

    if total_quantity  > 0 and items_tracked > 0:
      fresh_items_percentage = round((items_tracked / total_quantity) * 100, 1)
    else:
      fresh_items_percentage = 0.0
      
    if total_consummed_quantity > 0 and total_quantity  > 0 :
       percentage_consumed = round(( total_consummed_quantity/ total_quantity) * 100, 1)
    else:
        percentage_consumed = 0
        
    if total_wasted_food > 0 and total_quantity  > 0:
       percentage_expired = round(( total_wasted_food/ total_quantity) * 100, 1)
    else:
        percentage_expired = 0
     
     
    #  generate the consummed vs wated line graph
    
    year = date.today().year

    # 1) total items consumed per month (from ConsumptionLog)
    consumed_rows = (
        db.session.query(
            func.extract("month", ConsumptionLog.date).label("m"),
            func.sum(ConsumptionLog.qty_used).label("total_qty"),
        )
        .filter(
            ConsumptionLog.user_id == current_user.id,
            func.extract("year", ConsumptionLog.date) == year,
        )
        .group_by("m")
        .order_by("m")
        .all()
    )

    total_per_month = [0] * 12
    for m, total in consumed_rows:
        total_per_month[int(m) - 1] = float(total or 0)

    # 2) wasted items per month (from FoodWasted)
    wasted_rows = (
        db.session.query(
            func.extract("month", FoodWasted.expiry_date).label("m"),
            func.sum(FoodWasted.quantity).label("wasted_qty"),
        )
        .filter(
            FoodWasted.user_id == current_user.id,
            FoodWasted.expiry_date.isnot(None),
            func.extract("year", FoodWasted.expiry_date) == year,
        )
        .group_by("m")
        .order_by("m")
        .all()
    )

    wasted_per_month = [0] * 12
    for m, wasted in wasted_rows:
        wasted_per_month[int(m) - 1] = float(wasted or 0)

    
    
    #  generate the pie chart based on the categoies of the food items in th einventory
    
    # group by category and sum quantities
    rows = (
        db.session.query(
            Category.name.label("category"),
            func.sum(GroceryItem.quantity).label("total_qty"),
        )
        .join(GroceryItem, GroceryItem.category_id == Category.id)
        .filter(GroceryItem.user_id == current_user.id)
        .group_by(Category.name)
        .order_by(Category.name)
        .all()
    )

    labels = [r.category for r in rows]
    data = [float(r.total_qty or 0) for r in rows]
    
    return render_template('analytics.html', user=current_user, items_tracked=total_quantity, fresh_items_percentage=fresh_items_percentage, items_consumed_count=total_consummed_quantity, food_wasted = total_wasted_food, percentage_consumed = percentage_consumed, percentage_expired=percentage_expired, current_year=year,
        total_per_month=total_per_month,
        wasted_per_month=wasted_per_month,category_labels=labels,
        category_data=data,)
    


# Settings routes

@main.route('/setting', methods=["GET", "POST"])
@login_required
def setting():
     # ensure profile exists
    if not current_user.profile:
        current_user.profile = Profile()
        db.session.add(current_user.profile)
        db.session.commit()

    form = ProfileForm(obj=current_user.profile)

    if form.validate_on_submit():
        form.populate_obj(current_user.profile)

        # handle avatar upload if a file was selected
        file = form.avatar.data
        if file:
            filename = secure_filename(file.filename)
            ext = filename.rsplit(".", 1)[-1].lower()
            new_name = f"{uuid.uuid4().hex}.{ext}"
            upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], new_name)
            file.save(upload_path)

            # store path relative to /static so url_for('static', ...) works
            current_user.profile.avatar_url = f"avatars/{new_name}"

        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("main.setting"))

    return render_template("user_profile.html", form=form)
    

# change password route

@main.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        # verify current password
        if not current_user.check_password(form.current_password.data):
            flash("Current password is incorrect.", "danger")
            return redirect(url_for("main.change_password"))

        # set new password
        current_user.set_password(form.new_password.data)
        db.session.commit()

        flash("Your password has been updated.", "success")
        return redirect(url_for("main.change_password"))  # or wherever you like

    return render_template("change_password.html", form=form)


# Inventory Options Routes

@main.route('/inventory_options')
@login_required
def inventory_options():
    
    category_form = CategoryForm()
    location_form = LocationForm()
    units_form = UnitsForm()
    
    categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name).all()
    locations = Location.query.filter_by(user_id=current_user.id).order_by(Location.name).all()
    units = Units.query.filter_by(user_id=current_user.id).order_by(Units.name).all()
    return render_template('inventory_options.html', user=current_user, categories=categories, locations=locations, units=units, category_form=category_form, location_form=location_form, units_form=units_form)


# add unit route
@main.route('/add_unit', methods=['POST'])
@login_required
def add_unit():
    form = UnitsForm()
    if form.validate_on_submit():
        unit = Units(
            name=form.name.data,
            user_id=current_user.id
        )
        db.session.add(unit)
        db.session.commit()
        flash('Unit added successfully', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'error')
    return redirect(url_for('main.inventory_options'))


# delete unit route
@main.route('/delete_unit/<int:unit_id>', methods=['POST'])
@login_required
def delete_unit(unit_id):
    unit = Units.query.filter_by(id=unit_id, user_id=current_user.id).first_or_404()
    db.session.delete(unit)
    db.session.commit()
    flash('Unit deleted successfully', 'success')
    return redirect(url_for('main.inventory_options'))


# add location route
@main.route('/add_location', methods=['POST'])
@login_required
def add_location():
    form = LocationForm()
    if form.validate_on_submit():
        location = Location(
            name=form.name.data,
            user_id=current_user.id
        )
        db.session.add(location)
        db.session.commit()
        flash('Location added successfully', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'error')
    return redirect(url_for('main.inventory_options'))

# delete location route
@main.route('/delete_location/<int:location_id>', methods=['POST'])
@login_required
def delete_location(location_id):
    location = Location.query.filter_by(id=location_id, user_id=current_user.id).first_or_404()
    db.session.delete(location)
    db.session.commit()
    flash('Location deleted successfully', 'success')
    
    return redirect(url_for('main.inventory_options'))


# add category route
@main.route('/add_category', methods=['POST'])
@login_required
def add_category():
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            user_id=current_user.id
        )
        db.session.add(category)
        db.session.commit()
        flash('Category added successfully', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'error')
    return redirect(url_for('main.inventory_options'))

# delete category route
@main.route('/delete_category/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    category = Category.query.filter_by(id=category_id, user_id=current_user.id).first_or_404()
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted successfully', 'success')
    return redirect(url_for('main.inventory_options'))
    if item and field.data > item.quantity:
            raise ValidationError('Quantity used cannot exceed available quantity.')
            return redirect(url_for('main.inventory_options'))
            return redirect(url_for('main.inventory_options'))
    return redirect(url_for('main.inventory_options'))

