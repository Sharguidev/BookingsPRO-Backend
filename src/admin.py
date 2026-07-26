import os
from flask_admin import Admin
from models import db, User, Tenant, Service, Staff, Customer, Booking, Payment, EmailLog, StaffWorkingHours, StaffTimeOff, Plan
from flask_admin.contrib.sqla import ModelView

def setup_admin(app):
    app.secret_key = os.environ.get('FLASK_APP_KEY', 'sample key')
    app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
    admin = Admin(app, name='Sharguidev', template_mode='bootstrap3')

    
    # Add your models here, for example this is how we add a the User model to the admin
    admin.add_view(ModelView(User, db.session))
    admin.add_view(ModelView(Tenant, db.session))
    admin.add_view(ModelView(Service, db.session))
    admin.add_view(ModelView(Staff, db.session))
    admin.add_view(ModelView(Customer, db.session))
    admin.add_view(ModelView(Booking, db.session))
    admin.add_view(ModelView(Payment, db.session))
    admin.add_view(ModelView(EmailLog, db.session))
    admin.add_view(ModelView(StaffWorkingHours, db.session))
    admin.add_view(ModelView(StaffTimeOff, db.session))
    admin.add_view(ModelView(Plan, db.session))
    # You can duplicate that line to add mew models
    # admin.add_view(ModelView(YourModelName, db.session))