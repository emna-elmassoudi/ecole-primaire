import os
import time
import locale
from datetime import datetime, date, timedelta
from flask import Flask, render_template, redirect, url_for, flash, request, abort, jsonify, send_from_directory, session

try:
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'fr_FR')
    except:
        pass
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from PIL import Image as PILImage
import uuid
import mimetypes

from config import Config
from models import db, User, Announcement, Event, Circular, Photo, Notification, SiteSetting, Review, ContactMessage, Newsletter
from forms import LoginForm, RegisterForm, AnnouncementForm, EventForm, CircularForm, PhotoForm, ReviewForm, ContactForm

app = Flask(__name__)
app.config.from_object(Config)

CSRFProtect(app)
mail = Mail(app)
db.init_app(app)

HOME_IMAGES = ['hero_image', 'about_image', 'gallery_1', 'gallery_2', 'gallery_3', 'gallery_4', 'gallery_5', 'gallery_6']
HOME_IMAGE_DEFAULTS = {
    'hero_image': 'https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=600&q=80',
    'about_image': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&q=80',
    'gallery_1': 'https://images.unsplash.com/photo-1580582932707-520aed937b7b?w=600&q=80',
    'gallery_2': 'https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=600&q=80',
    'gallery_3': 'https://images.unsplash.com/photo-1571260899304-425eee4c7efc?w=600&q=80',
    'gallery_4': 'https://images.unsplash.com/photo-1588072432836-e10032774350?w=600&q=80',
    'gallery_5': 'https://images.unsplash.com/photo-1509062522246-3755977927d7?w=600&q=80',
    'gallery_6': 'https://images.unsplash.com/photo-1606768666853-403c90a981ad?w=600&q=80',
}
GALLERY_TITLES = {
    'gallery_1': "Notre école", 'gallery_2': "En classe", 'gallery_3': "Bibliothèque",
    'gallery_4': "Activités sportives", 'gallery_5': "Sorties scolaires", 'gallery_6': "Salle de classe",
}
GALLERY_LIGHTBOX = {
    'gallery_1': 'https://images.unsplash.com/photo-1580582932707-520aed937b7b?w=800&q=80',
    'gallery_2': 'https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=800&q=80',
    'gallery_3': 'https://images.unsplash.com/photo-1571260899304-425eee4c7efc?w=800&q=80',
    'gallery_4': 'https://images.unsplash.com/photo-1588072432836-e10032774350?w=800&q=80',
    'gallery_5': 'https://images.unsplash.com/photo-1509062522246-3755977927d7?w=800&q=80',
    'gallery_6': 'https://images.unsplash.com/photo-1606768666853-403c90a981ad?w=800&q=80',
}
app.permanent_session_lifetime = timedelta(minutes=30)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
ALLOWED_FILE_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'zip'}

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login', next=request.path))
        if current_user.role != 'admin':
            abort(404)
        return f(*args, **kwargs)
    return decorated_function

def save_file(file, subdir='uploads'):
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    filename = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], subdir)
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    if ext in ALLOWED_EXTENSIONS:
        img = PILImage.open(filepath)
        img.thumbnail((1200, 1200))
        img.save(filepath, optimize=True, quality=85)
    return f'uploads/{subdir}/{filename}'

def save_photo(file):
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    filename = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'photos')
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    img = PILImage.open(filepath)
    img.thumbnail((1920, 1920))
    img.save(filepath, optimize=True, quality=90)
    return f'uploads/photos/{filename}'

def create_notification(user_id, message, link=None, type='info'):
    notification = Notification(user_id=user_id, message=message, link=link, type=type)
    db.session.add(notification)
    db.session.commit()

def send_email_notification(user_email, subject, message, link, site_name, unsub_link=None):
    try:
        app.config['MAIL_SERVER'] = get_setting('mail_server', app.config.get('MAIL_SERVER', 'smtp.gmail.com'))
        app.config['MAIL_PORT'] = int(get_setting('mail_port', app.config.get('MAIL_PORT', 587)))
        app.config['MAIL_USERNAME'] = get_setting('mail_username', app.config.get('MAIL_USERNAME', ''))
        app.config['MAIL_PASSWORD'] = get_setting('mail_password', app.config.get('MAIL_PASSWORD', ''))
        app.config['MAIL_DEFAULT_SENDER'] = get_setting('mail_sender', app.config.get('MAIL_DEFAULT_SENDER', ''))
        with mail.connect() as conn:
            msg = Message(subject, recipients=[user_email])
            msg.html = render_template('emails/notification.html', site_name=site_name, title=subject, message=message, link=link, unsub_link=unsub_link)
            conn.send(msg)
    except Exception as e:
        print(f'Email send failed to {user_email}: {e}')

def notify_subscribers(message, link=None, type='info', subject=None):
    site_name = get_setting('site_name', 'École Primaire')
    base = url_for('index', _external=True).rstrip('/')
    full_link = base + (link or '') if link else base
    # Notify registered users
    for user in User.query.filter_by(is_subscribed=True).all():
        if user.role != 'admin':
            create_notification(user.id, message, link, type)
            if user.email:
                send_email_notification(user.email, subject or f'Nouveau - {site_name}', message, full_link, site_name)
    # Notify newsletter subscribers (visitors)
    for sub in Newsletter.query.all():
        unsub_link = url_for('newsletter_unsubscribe', token=sub.token, _external=True)
        send_email_notification(sub.email, subject or f'Nouveau - {site_name}', message, full_link, site_name, unsub_link)

def get_setting(key, default=''):
    setting = SiteSetting.query.filter_by(key=key).first()
    return setting.value if setting and setting.value is not None else default

MONTHS_FR = ['', 'janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']

@app.template_filter('date_fr')
def date_fr_filter(dt, format='%d %B %Y'):
    if not dt:
        return ''
    result = dt.strftime(format)
    for i, m in enumerate(MONTHS_FR):
        if m:
            result = result.replace(dt.strftime(f'%B' if i > 0 else ''), m)
    for i, m in enumerate(MONTHS_FR):
        if m:
            month_en = dt.strftime('%B') if i == dt.month else ''
            if month_en:
                result = result.replace(month_en, m)
    return result

@app.context_processor
def inject_globals():
    unread_count = 0
    latest_notifications = []
    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(user_id=current_user.id, read=False).count()
        latest_notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(5).all()
    latest_public = Announcement.query.filter_by(published=True).order_by(Announcement.created_at.desc()).first()
    home_images = {}
    for k in HOME_IMAGES:
        v = get_setting(k, '')
        home_images[k] = v if v and (v.startswith('/') or v.startswith('http')) else HOME_IMAGE_DEFAULTS.get(k, '')
    return {
        'site_name': get_setting('site_name', 'École Primaire'),
        'current_year': datetime.utcnow().year,
        'unread_count': unread_count,
        'latest_notifications': latest_notifications,
        'latest_public_announcement': latest_public,
        'home_images': home_images,
        'get_setting': get_setting
    }

@app.route('/health')
def health():
    return 'OK'

@app.route('/', methods=['GET', 'POST'])
def index():
    announcements = Announcement.query.filter_by(published=True).order_by(Announcement.created_at.desc()).limit(3).all()
    events = Event.query.filter_by(published=True).filter(Event.date >= date.today()).order_by(Event.date.asc()).limit(3).all()
    reviews = Review.query.filter_by(is_approved=True).order_by(Review.created_at.desc()).all()
    review_form = ReviewForm()
    if review_form.validate_on_submit() and current_user.is_authenticated:
        review = Review(
            user_id=current_user.id,
            name=current_user.username,
            rating=int(review_form.rating.data),
            comment=review_form.comment.data,
            is_approved=False
        )
        db.session.add(review)
        db.session.commit()
        flash('Merci pour votre avis ! Il sera publié après approbation.', 'success')
        return redirect(url_for('index', _anchor='testimonials'))
    return render_template('index.html', announcements=announcements, events=events, reviews=reviews, review_form=review_form)

@app.route('/annonces')
def announcements():
    page = request.args.get('page', 1, type=int)
    annonces = Announcement.query.filter_by(published=True).order_by(Announcement.created_at.desc()).paginate(page=page, per_page=9)
    return render_template('announcements.html', annonces=annonces)

@app.route('/annonces/<int:id>')
def announcement_detail(id):
    annonce = Announcement.query.get_or_404(id)
    if not annonce.published and not (current_user.is_authenticated and current_user.role == 'admin'):
        abort(404)
    other = Announcement.query.filter_by(published=True).filter(Announcement.id != id).order_by(Announcement.created_at.desc()).limit(3).all()
    return render_template('announcement_detail.html', annonce=annonce, other=other)

@app.route('/evenements')
def events():
    page = request.args.get('page', 1, type=int)
    events_list = Event.query.filter_by(published=True).filter(Event.date >= date.today()).order_by(Event.date.asc()).paginate(page=page, per_page=9)
    return render_template('events.html', events=events_list)

@app.route('/evenements/<int:id>')
def event_detail(id):
    event = Event.query.get_or_404(id)
    if not event.published and not (current_user.is_authenticated and current_user.role == 'admin'):
        abort(404)
    return render_template('event_detail.html', event=event)

@app.route('/circulaires')
def circulars():
    page = request.args.get('page', 1, type=int)
    circulars_list = Circular.query.filter_by(published=True).order_by(Circular.created_at.desc()).paginate(page=page, per_page=12)
    return render_template('circulars.html', circulars=circulars_list)

@app.route('/galerie')
def gallery():
    page = request.args.get('page', 1, type=int)
    photos = Photo.query.filter_by(published=True).order_by(Photo.created_at.desc()).paginate(page=page, per_page=12)
    return render_template('gallery.html', photos=photos)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        msg = ContactMessage(name=form.name.data, email=form.email.data, subject=form.subject.data, message=form.message.data)
        db.session.add(msg)
        db.session.commit()
        flash('Votre message a été envoyé avec succès. Nous vous répondrons dans les plus brefs délais.', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Cet email est déjà utilisé.', 'danger')
            return render_template('register.html', form=form)
        if User.query.filter_by(username=form.username.data).first():
            flash('Ce nom d\'utilisateur est déjà utilisé.', 'danger')
            return render_template('register.html', form=form)
        user = User(username=form.username.data, email=form.email.data, role='parent')
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Inscription réussie ! Bienvenue.', 'success')
        return redirect(url_for('index'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            flash('Connexion réussie.', 'success')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        flash('Email ou mot de passe incorrect.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('index'))

# Director secure login - URL secrète, connue uniquement du directeur
# Tentatives échouées stockées en session, lockout après 5 essais
LOGIN_ATTEMPTS_KEY = '_login_attempts'
LOGIN_LOCKOUT_TIME = 15 * 60  # 15 minutes

@app.route('/directeur', methods=['GET', 'POST'])
def directeur_login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('index'))
    now = time.time()
    attempts = session.get(LOGIN_ATTEMPTS_KEY, {'count': 0, 'first_attempt': now})
    if attempts['count'] >= 5 and (now - attempts['first_attempt']) < LOGIN_LOCKOUT_TIME:
        remaining = int(LOGIN_LOCKOUT_TIME - (now - attempts['first_attempt']))
        flash(f'Trop de tentatives. Réessayez dans {remaining // 60} minute(s).', 'danger')
        return render_template('directeur.html', form=LoginForm(), locked=True)
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.role == 'admin' and user.check_password(form.password.data):
            session.pop(LOGIN_ATTEMPTS_KEY, None)
            login_user(user)
            session.permanent = True
            flash('Bienvenue Monsieur le Directeur.', 'success')
            return redirect(url_for('admin_dashboard'))
        attempts['count'] += 1
        if attempts['count'] == 1:
            attempts['first_attempt'] = now
        session[LOGIN_ATTEMPTS_KEY] = attempts
        flash('Identifiants incorrects.', 'danger')
    return render_template('directeur.html', form=form, locked=False)

@app.route('/notifications')
@login_required
def notifications():
    page = request.args.get('page', 1, type=int)
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).paginate(page=page, per_page=20)
    Notification.query.filter_by(user_id=current_user.id, read=False).update({'read': True})
    db.session.commit()
    return render_template('notifications.html', notifications=notifs)

import secrets

@app.route('/newsletter/subscribe', methods=['POST'])
def newsletter_subscribe():
    email = request.form.get('email', '').strip().lower()
    if not email or '@' not in email:
        flash('Email invalide.', 'danger')
        return redirect(url_for('index', _anchor='hero'))
    if Newsletter.query.filter_by(email=email).first():
        flash('Vous êtes déjà abonné aux notifications.', 'info')
        return redirect(url_for('index', _anchor='hero'))
    sub = Newsletter(email=email, token=secrets.token_hex(32))
    db.session.add(sub)
    db.session.commit()
    flash('✅ Abonnement réussi ! Vous recevrez les notifications par email.', 'success')
    return redirect(url_for('index', _anchor='hero'))

@app.route('/newsletter/unsubscribe/<token>')
def newsletter_unsubscribe(token):
    sub = Newsletter.query.filter_by(token=token).first()
    if not sub:
        flash('Lien invalide.', 'danger')
        return redirect(url_for('index'))
    db.session.delete(sub)
    db.session.commit()
    flash('Vous êtes désabonné des notifications.', 'info')
    return redirect(url_for('index'))

@app.route('/parametres', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        if 'unsubscribe' in request.form:
            current_user.is_subscribed = False
            db.session.commit()
            flash('Vous ne recevrez plus de notifications.', 'info')
        elif 'subscribe' in request.form:
            current_user.is_subscribed = True
            db.session.commit()
            flash('Vous recevrez à nouveau les notifications.', 'success')
        return redirect(url_for('settings'))
    return render_template('settings.html')

# --- Admin Routes ---

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    total_annonces = Announcement.query.count()
    total_events = Event.query.count()
    total_circulars = Circular.query.count()
    total_photos = Photo.query.count()
    total_users = User.query.count()
    recent_annonces = Announcement.query.order_by(Announcement.created_at.desc()).limit(5).all()
    recent_events = Event.query.order_by(Event.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html',
        total_annonces=total_annonces, total_events=total_events,
        total_circulars=total_circulars, total_photos=total_photos,
        total_users=total_users, recent_annonces=recent_annonces,
        recent_events=recent_events)

@app.route('/admin/annonces')
@login_required
@admin_required
def admin_announcements():
    page = request.args.get('page', 1, type=int)
    annonces = Announcement.query.order_by(Announcement.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/announcements.html', annonces=annonces)

@app.route('/admin/annonces/nouvelle', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_announcement_new():
    form = AnnouncementForm()
    if form.validate_on_submit():
        annonce = Announcement(
            title=form.title.data,
            content=form.content.data,
            summary=form.summary.data,
            published=form.published.data,
            author_id=current_user.id
        )
        if form.image.data:
            annonce.image = save_file(form.image.data, 'announcements')
        db.session.add(annonce)
        db.session.commit()
        if annonce.published:
            notify_subscribers(f'Nouvelle annonce : {annonce.title}', url_for('announcement_detail', id=annonce.id), 'announcement')
        flash('Annonce créée avec succès.', 'success')
        return redirect(url_for('admin_announcements'))
    return render_template('admin/announcement_form.html', form=form, title='Nouvelle annonce')

@app.route('/admin/annonces/<int:id>/modifier', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_announcement_edit(id):
    annonce = Announcement.query.get_or_404(id)
    form = AnnouncementForm(obj=annonce)
    if form.validate_on_submit():
        annonce.title = form.title.data
        annonce.content = form.content.data
        annonce.summary = form.summary.data
        annonce.published = form.published.data
        if form.image.data:
            if annonce.image:
                old_path = os.path.join(app.config['UPLOAD_FOLDER'], annonce.image.replace('uploads/', ''))
                if os.path.exists(old_path):
                    os.remove(old_path)
            annonce.image = save_file(form.image.data, 'announcements')
        elif form.delete_image.data == '1' and annonce.image:
            old_path = os.path.join(app.config['UPLOAD_FOLDER'], annonce.image.replace('uploads/', ''))
            if os.path.exists(old_path):
                os.remove(old_path)
            annonce.image = None
        db.session.commit()
        if annonce.published:
            notify_subscribers(f'Annonce mise à jour : {annonce.title}', url_for('announcement_detail', id=annonce.id), 'announcement')
        flash('Annonce modifiée avec succès.', 'success')
        return redirect(url_for('admin_announcements'))
    form.published.data = annonce.published
    return render_template('admin/announcement_form.html', form=form, title='Modifier l\'annonce', annonce=annonce)

@app.route('/admin/annonces/<int:id>/supprimer', methods=['POST'])
@login_required
@admin_required
def admin_announcement_delete(id):
    annonce = Announcement.query.get_or_404(id)
    if annonce.image:
        path = os.path.join(app.config['UPLOAD_FOLDER'], annonce.image.replace('uploads/', ''))
        if os.path.exists(path):
            os.remove(path)
    db.session.delete(annonce)
    db.session.commit()
    flash('Annonce supprimée.', 'success')
    return redirect(url_for('admin_announcements'))

@app.route('/admin/evenements')
@login_required
@admin_required
def admin_events():
    page = request.args.get('page', 1, type=int)
    events_list = Event.query.order_by(Event.date.desc()).paginate(page=page, per_page=20)
    return render_template('admin/events.html', events=events_list)

@app.route('/admin/evenements/nouveau', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_event_new():
    form = EventForm()
    if form.validate_on_submit():
        event = Event(
            title=form.title.data,
            description=form.description.data,
            date=form.date.data,
            time=form.time.data,
            location=form.location.data,
            published=form.published.data,
            author_id=current_user.id
        )
        if form.image.data:
            event.image = save_file(form.image.data, 'events')
        db.session.add(event)
        db.session.commit()
        if event.published:
            notify_subscribers(f'Nouvel événement : {event.title} le {event.date.strftime("%d/%m/%Y")}', url_for('event_detail', id=event.id), 'event')
        flash('Événement créé avec succès.', 'success')
        return redirect(url_for('admin_events'))
    return render_template('admin/event_form.html', form=form, title='Nouvel événement')

@app.route('/admin/evenements/<int:id>/modifier', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_event_edit(id):
    event = Event.query.get_or_404(id)
    form = EventForm(obj=event)
    if form.validate_on_submit():
        event.title = form.title.data
        event.description = form.description.data
        event.date = form.date.data
        event.time = form.time.data
        event.location = form.location.data
        event.published = form.published.data
        if form.image.data:
            if event.image:
                old_path = os.path.join(app.config['UPLOAD_FOLDER'], event.image.replace('uploads/', ''))
                if os.path.exists(old_path):
                    os.remove(old_path)
            event.image = save_file(form.image.data, 'events')
        db.session.commit()
        if event.published:
            notify_subscribers(f'Événement mis à jour : {event.title}', url_for('event_detail', id=event.id), 'event')
        flash('Événement modifié avec succès.', 'success')
        return redirect(url_for('admin_events'))
    form.published.data = event.published
    return render_template('admin/event_form.html', form=form, title='Modifier l\'événement', event=event)

@app.route('/admin/evenements/<int:id>/supprimer', methods=['POST'])
@login_required
@admin_required
def admin_event_delete(id):
    event = Event.query.get_or_404(id)
    if event.image:
        path = os.path.join(app.config['UPLOAD_FOLDER'], event.image.replace('uploads/', ''))
        if os.path.exists(path):
            os.remove(path)
    db.session.delete(event)
    db.session.commit()
    flash('Événement supprimé.', 'success')
    return redirect(url_for('admin_events'))

@app.route('/admin/circulaires')
@login_required
@admin_required
def admin_circulars():
    page = request.args.get('page', 1, type=int)
    circulars_list = Circular.query.order_by(Circular.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/circulars.html', circulars=circulars_list)

@app.route('/admin/circulaires/nouveau', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_circular_new():
    form = CircularForm()
    if form.validate_on_submit():
        if not form.file.data:
            flash('Veuillez sélectionner un fichier.', 'danger')
            return render_template('admin/circular_form.html', form=form, title='Nouvelle circulaire')
        circular = Circular(
            title=form.title.data,
            description=form.description.data,
            published=form.published.data,
            author_id=current_user.id
        )
        file = form.file.data
        circular.file_path = save_file(file, 'circulars')
        circular.file_size = os.path.getsize(os.path.join(app.config['UPLOAD_FOLDER'], circular.file_path.replace('uploads/', '')))
        db.session.add(circular)
        db.session.commit()
        if circular.published:
            notify_subscribers(f'Nouvelle circulaire : {circular.title}', url_for('circulars'), 'circular')
        flash('Circulaire publiée avec succès.', 'success')
        return redirect(url_for('admin_circulars'))
    return render_template('admin/circular_form.html', form=form, title='Nouvelle circulaire')

@app.route('/admin/circulaires/<int:id>/modifier', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_circular_edit(id):
    circular = Circular.query.get_or_404(id)
    form = CircularForm(obj=circular)
    if form.validate_on_submit():
        circular.title = form.title.data
        circular.description = form.description.data
        circular.published = form.published.data
        if form.file.data:
            if circular.file_path:
                old_path = os.path.join(app.config['UPLOAD_FOLDER'], circular.file_path.replace('uploads/', ''))
                if os.path.exists(old_path):
                    os.remove(old_path)
            circular.file_path = save_file(form.file.data, 'circulars')
            circular.file_size = os.path.getsize(os.path.join(app.config['UPLOAD_FOLDER'], circular.file_path.replace('uploads/', '')))
        db.session.commit()
        if circular.published:
            notify_subscribers(f'Circulaire mise à jour : {circular.title}', url_for('circulars'), 'circular')
        flash('Circulaire modifiée avec succès.', 'success')
        return redirect(url_for('admin_circulars'))
    form.published.data = circular.published
    return render_template('admin/circular_form.html', form=form, title='Modifier la circulaire', circular=circular)

@app.route('/admin/circulaires/<int:id>/supprimer', methods=['POST'])
@login_required
@admin_required
def admin_circular_delete(id):
    circular = Circular.query.get_or_404(id)
    if circular.file_path:
        path = os.path.join(app.config['UPLOAD_FOLDER'], circular.file_path.replace('uploads/', ''))
        if os.path.exists(path):
            os.remove(path)
    db.session.delete(circular)
    db.session.commit()
    flash('Circulaire supprimée.', 'success')
    return redirect(url_for('admin_circulars'))

@app.route('/admin/photos')
@login_required
@admin_required
def admin_photos():
    page = request.args.get('page', 1, type=int)
    photos_list = Photo.query.order_by(Photo.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/photos.html', photos=photos_list)

@app.route('/admin/photos/ajouter', methods=['POST'])
@login_required
@admin_required
def admin_photo_add():
    form = PhotoForm()
    if form.validate_on_submit():
        if form.image.data:
            photo = Photo(
                title=form.title.data or '',
                description=form.description.data or '',
                image_path=save_photo(form.image.data),
                published=True,
                author_id=current_user.id
            )
            db.session.add(photo)
            db.session.commit()
            notify_subscribers('Nouvelle photo ajoutée à la galerie', url_for('gallery'), 'photo')
            flash('Photo ajoutée avec succès.', 'success')
        else:
            flash('Veuillez sélectionner une image.', 'danger')
    return redirect(url_for('admin_photos'))

@app.route('/admin/photos/<int:id>/supprimer', methods=['POST'])
@login_required
@admin_required
def admin_photo_delete(id):
    photo = Photo.query.get_or_404(id)
    if photo.image_path:
        path = os.path.join(app.config['UPLOAD_FOLDER'], photo.image_path.replace('uploads/', ''))
        if os.path.exists(path):
            os.remove(path)
    db.session.delete(photo)
    db.session.commit()
    flash('Photo supprimée.', 'success')
    return redirect(url_for('admin_photos'))

@app.route('/admin/utilisateurs')
@login_required
@admin_required
def admin_users():
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/users.html', users=users)

@app.route('/admin/utilisateurs/<int:id>/toggle-subscription', methods=['POST'])
@login_required
@admin_required
def admin_toggle_subscription(id):
    user = User.query.get_or_404(id)
    user.is_subscribed = not user.is_subscribed
    db.session.commit()
    flash(f'Abonnement de {user.username} {"activé" if user.is_subscribed else "désactivé"}.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/utilisateurs/<int:id>/supprimer', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(id):
    if id == current_user.id:
        flash('Vous ne pouvez pas vous supprimer vous-même.', 'danger')
        return redirect(url_for('admin_users'))
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    flash(f'Utilisateur {user.username} supprimé.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/parametres', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_settings():
    if request.method == 'POST':
        for key in ['site_name', 'site_description', 'about_text', 'contact_email', 'contact_phone', 'contact_address', 'school_hours', 'mail_server', 'mail_port', 'mail_username', 'mail_password', 'mail_sender'] + HOME_IMAGES:
            value = request.form.get(key, '')
            setting = SiteSetting.query.filter_by(key=key).first()
            if setting:
                setting.value = value
            else:
                db.session.add(SiteSetting(key=key, value=value))
        db.session.commit()
        flash('Paramètres enregistrés.', 'success')
        return redirect(url_for('admin_settings'))
    settings = {s.key: s.value for s in SiteSetting.query.all()}
    home_images = {k: settings.get(k, HOME_IMAGE_DEFAULTS.get(k, '')) for k in HOME_IMAGES}
    return render_template('admin/settings.html', settings=settings, home_images=home_images)

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    app.logger.error(f'500 error: {e}')
    import traceback
    app.logger.error(traceback.format_exc())
    return render_template('500.html'), 500

@app.route('/admin/messages')
@login_required
@admin_required
def admin_messages():
    page = request.args.get('page', 1, type=int)
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/messages.html', messages=messages)

@app.route('/admin/messages/<int:id>/lire', methods=['POST'])
@login_required
@admin_required
def admin_message_read(id):
    msg = ContactMessage.query.get_or_404(id)
    msg.read = True
    db.session.commit()
    flash('Message marqué comme lu.', 'success')
    return redirect(url_for('admin_messages'))

@app.route('/admin/messages/<int:id>/supprimer', methods=['POST'])
@login_required
@admin_required
def admin_message_delete(id):
    msg = ContactMessage.query.get_or_404(id)
    db.session.delete(msg)
    db.session.commit()
    flash('Message supprimé.', 'success')
    return redirect(url_for('admin_messages'))

@app.route('/admin/newsletter')
@login_required
@admin_required
def admin_newsletter():
    page = request.args.get('page', 1, type=int)
    subs = Newsletter.query.order_by(Newsletter.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/newsletter.html', subs=subs)

@app.route('/admin/newsletter/<int:id>/supprimer', methods=['POST'])
@login_required
@admin_required
def admin_newsletter_delete(id):
    sub = Newsletter.query.get_or_404(id)
    db.session.delete(sub)
    db.session.commit()
    flash('Abonné supprimé.', 'success')
    return redirect(url_for('admin_newsletter'))

@app.route('/admin/upload-home-image', methods=['POST'])
@login_required
@admin_required
def admin_upload_home_image():
    key = request.form.get('key', '')
    if key not in HOME_IMAGES:
        flash('Image invalide.', 'danger')
        return redirect(url_for('admin_settings', _anchor='images'))
    file = request.files.get('image')
    if not file or not file.filename:
        flash('Veuillez sélectionner une image.', 'danger')
        return redirect(url_for('admin_settings', _anchor='images'))
    path = save_file(file, 'home')
    setting = SiteSetting.query.filter_by(key=key).first()
    if setting:
        setting.value = url_for('static', filename=path)
    else:
        db.session.add(SiteSetting(key=key, value=url_for('static', filename=path)))
    db.session.commit()
    flash('Image mise à jour.', 'success')
    return redirect(url_for('admin_settings', _anchor='images'))

@app.route('/admin/avis')
@login_required
@admin_required
def admin_reviews():
    page = request.args.get('page', 1, type=int)
    reviews = Review.query.order_by(Review.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/reviews.html', reviews=reviews)

@app.route('/admin/avis/<int:id>/approuver', methods=['POST'])
@login_required
@admin_required
def admin_review_approve(id):
    review = Review.query.get_or_404(id)
    review.is_approved = True
    db.session.commit()
    flash('Avis approuvé et publié.', 'success')
    return redirect(url_for('admin_reviews'))

@app.route('/admin/avis/<int:id>/supprimer', methods=['POST'])
@login_required
@admin_required
def admin_review_delete(id):
    review = Review.query.get_or_404(id)
    db.session.delete(review)
    db.session.commit()
    flash('Avis supprimé.', 'success')
    return redirect(url_for('admin_reviews'))


