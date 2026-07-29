from app import app, db
from models import User

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(role='admin').first():
            admin = User(username='directeur', email='directeur@ecole-primaire.fr', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print('Compte administrateur créé : directeur / admin123')
        print('Base de données initialisée.')
    app.run(debug=True, host='0.0.0.0', port=8080)
