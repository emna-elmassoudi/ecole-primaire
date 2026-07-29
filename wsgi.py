import os
from app import app, db
from models import User

os.makedirs(os.path.join(app.instance_path), exist_ok=True)

upload_dir = os.path.join(app.root_path, 'static', 'uploads', 'home')
os.makedirs(upload_dir, exist_ok=True)

with app.app_context():
    db.create_all()
    if not User.query.filter_by(role='admin').first():
        admin = User(username='directeur', email='directeur@ecole-primaire.fr', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
