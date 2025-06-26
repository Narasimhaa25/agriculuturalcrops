from werkzeug.security import generate_password_hash
from models import db, Admin
from app import app

with app.app_context():
    db.create_all()
    username = 'admin'
    password = 'admin123'  # Change this
    hashed_password = generate_password_hash(password)

    if not Admin.query.filter_by(username=username).first():
        new_admin = Admin(username=username, password=hashed_password)
        db.session.add(new_admin)
        db.session.commit()
        print("✅ Admin user created.")
    else:
        print("ℹ️ Admin user already exists.")