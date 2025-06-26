# check_admin.py
from models import db, Admin
from app import app

with app.app_context():
    admin = Admin.query.first()
    if admin:
        print(f"Admin exists: {admin.username}")
    else:
        print("❌ No admin user found.")