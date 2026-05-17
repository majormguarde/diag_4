import os
from flask import render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User, Content

def register_routes(app):
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/profile')
    def profile():
        user_id = request.args.get('user_id')
        if not user_id:
            return render_template('index.html', error="Укажите параметр user_id")
        try:
            telegram_id = int(user_id)
        except ValueError:
            return render_template('index.html', error="Неверный формат ID")
        
        user = User.query.filter_by(telegram_id=telegram_id).first()
        if not user:
            return render_template('index.html', error="Пользователь не найден. Сначала зарегистрируйтесь в боте через /start")
        
        if user.profile_completed:
            return redirect(url_for('cabinet', user_id=user.telegram_id))
        
        return render_template('profile.html', user=user)
    
    @app.route('/profile', methods=['POST'])
    def profile_post():
        user_id = request.args.get('user_id')
        if not user_id:
            return render_template('index.html', error="Укажите параметр user_id")
        try:
            telegram_id = int(user_id)
        except ValueError:
            return render_template('index.html', error="Неверный формат ID")
        
        user = User.query.filter_by(telegram_id=telegram_id).first()
        if not user:
            return render_template('index.html', error="Пользователь не найден. Сначала зарегистрируйтесь в боте через /start")
        
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        login = request.form.get('login')
        password = request.form.get('password')
        
        if not first_name or not phone or not email or not login or not password:
            return render_template('profile.html', user=user, error="Пожалуйста, заполните все обязательные поля")
        
        existing_user = User.query.filter_by(login=login).first()
        if existing_user and existing_user.id != user.id:
            return render_template('profile.html', user=user, error="Этот логин уже занят")
        
        user.first_name = first_name
        user.last_name = last_name
        user.phone = phone
        user.email = email
        user.login = login
        user.password_hash = generate_password_hash(password)
        user.profile_completed = True
        
        db.session.commit()
        flash("Персональные данные успешно сохранены!")
        return redirect(url_for('cabinet', user_id=user.telegram_id))
    
    @app.route('/logout')
    def logout():
        return redirect(url_for('index'))
    
    @app.route('/cabinet')
    def cabinet():
        user_id = request.args.get('user_id')
        if not user_id:
            return render_template('index.html', error="Укажите параметр user_id")
        try:
            telegram_id = int(user_id)
        except ValueError:
            return render_template('index.html', error="Неверный формат ID")
        
        user = User.query.filter_by(telegram_id=telegram_id).first()
        if not user:
            return render_template('index.html', error="Пользователь не найден. Сначала зарегистрируйтесь в боте через /start")
        
        if not user.profile_completed:
            return redirect(url_for('profile', user_id=user.telegram_id))
        
        contents = Content.query.filter_by(user_id=user.id).order_by(Content.created_at.desc()).all()
        return render_template('cabinet.html', user=user, contents=contents)
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'GET':
            return render_template('login.html')
        
        login = request.form.get('login')
        password = request.form.get('password')
        
        user = User.query.filter_by(login=login).first()
        if not user or not check_password_hash(user.password_hash, password):
            return render_template('login.html', error="Неверный логин или пароль")
        
        return redirect(url_for('cabinet', user_id=user.telegram_id))
    
    @app.route('/examples/<filename>')
    def examples(filename):
        """Маршрут для скачивания файлов примеров из папки _examples"""
        examples_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_examples')
        return send_from_directory(examples_dir, filename, as_attachment=True)