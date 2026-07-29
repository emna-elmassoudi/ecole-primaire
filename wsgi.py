import os
import sys
import traceback
from sqlalchemy.exc import IntegrityError

try:
    from app import app, db
    from models import User
except Exception as e:
    print("IMPORT ERROR:", e, file=sys.stderr)
    traceback.print_exc()
    raise

os.makedirs(os.path.join(app.instance_path), exist_ok=True)

upload_dir = os.path.join(app.root_path, 'static', 'uploads', 'home')
os.makedirs(upload_dir, exist_ok=True)

with app.app_context():
    try:
        db.create_all()
        if not User.query.filter_by(role='admin').first():
            admin = User(username='directeur', email='directeur@ecole-primaire.fr', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Admin account created")
        else:
            print("Admin already exists")
    except IntegrityError:
        db.session.rollback()
        print("Admin creation skipped (already exists)")
    except Exception as e:
        print("DB INIT ERROR:", e, file=sys.stderr)
        traceback.print_exc()
        raise
