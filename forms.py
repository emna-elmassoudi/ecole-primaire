from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, BooleanField, PasswordField, DateField, SelectField, HiddenField
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])

class RegisterForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired(), Length(min=2, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmer le mot de passe', validators=[DataRequired(), EqualTo('password')])

class AnnouncementForm(FlaskForm):
    title = StringField('Titre', validators=[DataRequired(), Length(max=200)])
    summary = StringField('Résumé', validators=[Optional(), Length(max=300)])
    content = TextAreaField('Contenu', validators=[DataRequired()])
    image = FileField('Image', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'])])
    published = BooleanField('Publier')
    delete_image = HiddenField()

class EventForm(FlaskForm):
    title = StringField('Titre', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[DataRequired()])
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    time = StringField('Heure', validators=[Optional(), Length(max=10)])
    location = StringField('Lieu', validators=[Optional(), Length(max=200)])
    image = FileField('Image', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'])])
    published = BooleanField('Publier')

class CircularForm(FlaskForm):
    title = StringField('Titre', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Optional()])
    file = FileField('Fichier (PDF, Word, etc.)', validators=[FileAllowed(['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'zip'])])
    published = BooleanField('Publier')

class PhotoForm(FlaskForm):
    title = StringField('Titre', validators=[Optional(), Length(max=200)])
    description = TextAreaField('Description', validators=[Optional()])
    image = FileField('Image', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'])])

class ReviewForm(FlaskForm):
    rating = SelectField('Note', choices=[('5', '5 ★★★★★'), ('4', '4 ★★★★☆'), ('3', '3 ★★★☆☆'), ('2', '2 ★★☆☆☆'), ('1', '1 ★☆☆☆☆')], validators=[DataRequired()])
    comment = TextAreaField('Votre avis', validators=[DataRequired(), Length(min=10, max=500)])

class ContactForm(FlaskForm):
    name = StringField('Nom', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    subject = StringField('Sujet', validators=[DataRequired(), Length(max=200)])
    message = TextAreaField('Message', validators=[DataRequired()])
