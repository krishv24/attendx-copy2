# app/auth/routes.py - Handles user authentication and initial setup
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from werkzeug.security import check_password_hash
import os

from app.auth import auth
from app.models import User, Config
from app import models as app_models
from app.extensions import db
from dotenv import load_dotenv

load_dotenv()

@auth.route('/setup-key', methods=['GET', 'POST'])
def setup_key():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    # Check if key already exists
    try:
        if Config.query.filter_by(key='gemini_api_key').first():
            return redirect(url_for('auth.login'))
    except Exception:
        pass # db error

    if request.method == 'POST':
        api_key_value = request.form.get('api_key')
        if api_key_value:
            new_config = Config(key='gemini_api_key', value=api_key_value)
            try:
                db.session.add(new_config)
                db.session.commit()
                flash('API Key saved successfully.', 'success')
                return redirect(url_for('auth.login'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error saving API Key: {e}', 'danger')
        else:
            flash('Please enter an API Key.', 'danger')
            
    # Pre-fill from .env if available
    default_key = os.environ.get('GEMINI_API_KEY', '')
    return render_template('setup_key.html', default_key=default_key)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('student.dashboard'))
        
    # Check if API Key setup is required
    try:
        api_key = Config.query.filter_by(key='gemini_api_key').first()
        if not api_key:
            return redirect(url_for('auth.setup_key'))
    except Exception:
        pass
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            flash('Please check your login details and try again.', 'danger')
            return redirect(url_for('auth.login'))
            
        login_user(user, remember=remember)
        if user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('student.dashboard'))
        
    return render_template('login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        roll_number = request.form.get('roll_number')
        password = request.form.get('password')
        
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register'))
            
        student_exists = app_models.Student.query.filter_by(roll_number=roll_number).first()
        if student_exists:
            flash('Roll Number already exists.', 'danger')
            return redirect(url_for('auth.register'))
            
        new_student = app_models.Student(
            name=name,
            roll_number=roll_number,
            department='General',
            semester=1,
            email=email,
            risk_score='Low',
            predicted_attendance=100.0
        )
        db.session.add(new_student)
        db.session.flush() # get id
        
        from werkzeug.security import generate_password_hash
        new_user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role='student',
            student_id=new_student.id
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('register.html')

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
