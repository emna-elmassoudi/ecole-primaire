from app import app, db
from models import User

with app.app_context():
    db.create_all()
    if not User.query.filter_by(role='admin').first():
        admin = User(username='directeur', email='directeur@ecole-primaire.fr', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
