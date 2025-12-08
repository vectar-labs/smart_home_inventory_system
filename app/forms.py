import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, DateField, SelectField, ValidationError
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange
from flask_wtf.file import FileField, FileAllowed
from app.models import User, Category, Location, Units, GroceryItem


# User Registration Form
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=120)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    submit = SubmitField('Sign Up')
    
# User Login Form
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class GroceryItemForm(FlaskForm):
    name = StringField('Item Name', validators=[DataRequired()])
    category_id = SelectField('Category', coerce=int)
    quantity = FloatField('Quantity', validators=[DataRequired(), NumberRange(min=0)])
    expiry_date = DateField('Expiry Date', format='%Y-%m-%d')
    purchase_date = DateField('Purchase Date', format='%Y-%m-%d')
    location_id = SelectField('Location', coerce=int)
    unit_id = SelectField('Unit', coerce=int)
    barcode = StringField('Barcode')
    photo = FileField('Photo', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Save Item')
    
# Edit Grocery Item Form
class EditGroceryItemForm(FlaskForm):
    name = StringField('Item Name', validators=[DataRequired()])
    category_id = SelectField('Category', coerce=int)
    quantity = FloatField('Quantity', validators=[DataRequired(), NumberRange(min=0)])
    expiry_date = DateField('Expiry Date', format='%Y-%m-%d')
    purchase_date = DateField('Purchase Date', format='%Y-%m-%d')
    location_id = SelectField('Location', coerce=int)
    unit_id = SelectField('Unit', coerce=int)
    barcode = StringField('Barcode')
    photo = FileField('Photo', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update Item')


class ConsumptionLogForm(FlaskForm):
    grocery_item_id = SelectField('Grocery Item', coerce=int)
    date = DateField('Date Used', format='%Y-%m-%d', default=datetime.date.today())
    qty_used = FloatField('Quantity Used', validators=[DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField('Log Usage')
    
    def validate_qty_used(self, field):
        item = GroceryItem.query.get(self.grocery_item_id.data)
        if item and field.data > item.quantity:
            raise ValidationError('Quantity used cannot exceed available quantity.')
        
# edit consumption log form
class EditConsumptionLogForm(FlaskForm):
    grocery_item_id = SelectField('Grocery Item', coerce=int)
    date = DateField('Date Used', format='%Y-%m-%d')
    qty_used = FloatField('Quantity Used', validators=[DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField('Update Log')
    
    def validate_qty_used(self, field):
        item = GroceryItem.query.get(self.grocery_item_id.data)
        if item and field.data > item.quantity:
            raise ValidationError('Quantity used cannot exceed available quantity.')
        