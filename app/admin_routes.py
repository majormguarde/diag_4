from flask import render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User, Content, Admin
from datetime import datetime

def register_admin_routes(app):
    @app.route('/admin')
    def admin_dashboard():
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        admin = Admin.query.get(session['admin_id'])
        if not admin:
            return redirect(url_for('admin_login'))
        
        # Статистика
        total_users = User.query.count()
        total_contents = Content.query.count()
        total_admins = Admin.query.count()
        total_photos = Content.query.filter_by(type='photo').count()
        total_videos = Content.query.filter_by(type='video').count()
        total_links = Content.query.filter_by(type='link').count()
        
        # Последние пользователи
        recent_users = User.query.order_by(User.registered_at.desc()).limit(10).all()
        
        stats = {
            'total_users': total_users,
            'total_contents': total_contents,
            'total_admins': total_admins,
            'total_photos': total_photos,
            'total_videos': total_videos,
            'total_links': total_links
        }
        
        return render_template('admin/dashboard.html', title='Главная', admin=admin, stats=stats, recent_users=recent_users)
    
    @app.route('/admin/users')
    def admin_users():
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        admin = Admin.query.get(session['admin_id'])
        if not admin:
            return redirect(url_for('admin_login'))
        
        users = User.query.order_by(User.registered_at.desc()).all()
        return render_template('admin/users.html', title='Пользователи', admin=admin, users=users)
    
    @app.route('/admin/contents')
    def admin_contents():
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        admin = Admin.query.get(session['admin_id'])
        if not admin:
            return redirect(url_for('admin_login'))
        
        contents = Content.query.order_by(Content.created_at.desc()).all()
        return render_template('admin/contents.html', title='Контент', admin=admin, contents=contents)
    
    @app.route('/admin/admins')
    def admin_admins():
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        admin = Admin.query.get(session['admin_id'])
        if not admin:
            return redirect(url_for('admin_login'))
        
        admins = Admin.query.order_by(Admin.created_at.desc()).all()
        return render_template('admin/admins.html', title='Администраторы', admin=admin, admins=admins)
    
    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        if request.method == 'GET':
            return render_template('admin/login.html', title='Вход в админку')
        
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        if not admin or not admin.check_password(password):
            return render_template('admin/login.html', title='Вход в админку', error='Неверный логин или пароль')
        
        session['admin_id'] = admin.id
        return redirect(url_for('admin_dashboard'))
    
    @app.route('/admin/logout')
    def admin_logout():
        session.pop('admin_id', None)
        return redirect(url_for('admin_login'))
    
    @app.route('/admin/create-admin', methods=['GET', 'POST'])
    def admin_create():
        """Создание первого администратора (суперадмина)"""
        if Admin.query.first():
            return redirect(url_for('admin_login'))
        
        if request.method == 'GET':
            return render_template('admin/create_admin.html', title='Создание администратора')
        
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        if not username or not password:
            return render_template('admin/create_admin.html', title='Создание администратора', error='Логин и пароль обязательны')
        
        existing_admin = Admin.query.filter_by(username=username).first()
        if existing_admin:
            return render_template('admin/create_admin.html', title='Создание администратора', error='Этот логин уже занят')
        
        new_admin = Admin(
            username=username,
            password_hash=generate_password_hash(password),
            email=email,
            is_superadmin=True
        )
        
        db.session.add(new_admin)
        db.session.commit()
        
        flash('Администратор успешно создан! Теперь вы можете войти в систему.')
        return redirect(url_for('admin_login'))
    
    # ==================== CRUD для Пользователей ====================
    
    @app.route('/admin/users/create', methods=['GET', 'POST'])
    def admin_user_create():
        """Создание нового пользователя"""
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        admin = Admin.query.get(session['admin_id'])
        if not admin:
            return redirect(url_for('admin_login'))
        
        if request.method == 'GET':
            return render_template('admin/user_form.html', title='Создание пользователя', admin=admin, user=None)
        
        telegram_id = request.form.get('telegram_id')
        username = request.form.get('username')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        login = request.form.get('login')
        password = request.form.get('password')
        
        # Проверка уникальности telegram_id
        if telegram_id and User.query.filter_by(telegram_id=int(telegram_id)).first():
            return render_template('admin/user_form.html', title='Создание пользователя', admin=admin, user=None,
                                 error='Пользователь с таким Telegram ID уже существует')
        
        # Проверка уникальности login
        if login and User.query.filter_by(login=login).first():
            return render_template('admin/user_form.html', title='Создание пользователя', admin=admin, user=None,
                                 error='Пользователь с таким логином уже существует')
        
        new_user = User(
            telegram_id=int(telegram_id) if telegram_id else None,
            username=username,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email=email,
            login=login,
            password_hash=generate_password_hash(password) if password else None,
            profile_completed=True
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Пользователь успешно создан!', 'success')
        return redirect(url_for('admin_users'))
    
    @app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
    def admin_user_edit(user_id):
        """Редактирование пользователя"""
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        admin = Admin.query.get(session['admin_id'])
        if not admin:
            return redirect(url_for('admin_login'))
        
        user = User.query.get_or_404(user_id)
        
        if request.method == 'GET':
            return render_template('admin/user_form.html', title='Редактирование пользователя', admin=admin, user=user)
        
        telegram_id = request.form.get('telegram_id')
        username = request.form.get('username')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        login = request.form.get('login')
        password = request.form.get('password')
        
        # Проверка уникальности telegram_id (исключая текущего пользователя)
        if telegram_id:
            existing = User.query.filter_by(telegram_id=int(telegram_id)).first()
            if existing and existing.id != user_id:
                return render_template('admin/user_form.html', title='Редактирование пользователя', admin=admin, user=user,
                                     error='Пользователь с таким Telegram ID уже существует')
        
        # Проверка уникальности login (исключая текущего пользователя)
        if login:
            existing = User.query.filter_by(login=login).first()
            if existing and existing.id != user_id:
                return render_template('admin/user_form.html', title='Редактирование пользователя', admin=admin, user=user,
                                     error='Пользователь с таким логином уже существует')
        
        user.telegram_id = int(telegram_id) if telegram_id else None
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.phone = phone
        user.email = email
        user.login = login
        if password:
            user.password_hash = generate_password_hash(password)
        user.profile_completed = True
        
        db.session.commit()
        
        flash('Пользователь успешно обновлен!', 'success')
        return redirect(url_for('admin_users'))
    
    @app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
    def admin_user_delete(user_id):
        """Удаление пользователя"""
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        admin = Admin.query.get(session['admin_id'])
        if not admin:
            return redirect(url_for('admin_login'))
        
        user = User.query.get_or_404(user_id)
        
        db.session.delete(user)
        db.session.commit()
        
        flash('Пользователь успешно удален!', 'success')
        return redirect(url_for('admin_users'))
    
    # ==================== CRUD для Контента ====================
    
    @app.route('/admin/contents/create', methods=['GET', 'POST'])
    def admin_content_create():
        """Создание нового контента"""
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        admin = Admin.query.get(session['admin_id'])
        if not admin:
            return redirect(url_for('admin_login'))
        
        users = User.query.order_by(User.username).all()
        
        if request.method == 'GET':
            return render_template('admin/content_form.html', title='Создание контента', admin=admin, content=None, users=users)
        
        user_id = request.form.get('user_id')
        content_type = request.form.get('type')
        content = request.form.get('content')
        file_id = request.form.get('file_id')
        local_path = request.form.get('local_path')
        
        new_content = Content(
            user_id=int(user_id),
            type=content_type,
            content=content,
            file_id=file_id,
            local_path=local_path
        )
        
        db.session.add(new_content)
        db.session.commit()
        
        flash('Контент успешно создан!', 'success')
        return redirect(url_for('admin_contents'))
    
    @app.route('/admin/contents/edit/<int:content_id>', methods=['GET', 'POST'])
    def admin_content_edit(content_id):
        """Редактирование контента"""
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        admin = Admin.query.get(session['admin_id'])
        if not admin:
            return redirect(url_for('admin_login'))
        
        content = Content.query.get_or_404(content_id)
        users = User.query.order_by(User.username).all()
        
        if request.method == 'GET':
            return render_template('admin/content_form.html', title='Редактирование контента', admin=admin, content=content, users=users)
        
        user_id = request.form.get('user_id')
        content_type = request.form.get('type')
        content_text = request.form.get('content')
        file_id = request.form.get('file_id')
        local_path = request.form.get('local_path')
        
        content.user_id = int(user_id)
        content.type = content_type
        content.content = content_text
        content.file_id = file_id
        content.local_path = local_path
        
        db.session.commit()
        
        flash('Контент успешно обновлен!', 'success')
        return redirect(url_for('admin_contents'))
    
    @app.route('/admin/contents/delete/<int:content_id>', methods=['POST'])
    def admin_content_delete(content_id):
        """Удаление контента"""
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        admin = Admin.query.get(session['admin_id'])
        if not admin:
            return redirect(url_for('admin_login'))
        
        content = Content.query.get_or_404(content_id)
        
        db.session.delete(content)
        db.session.commit()
        
        flash('Контент успешно удален!', 'success')
        return redirect(url_for('admin_contents'))
    
    # ==================== CRUD для Администраторов ====================
    
    @app.route('/admin/admins/create', methods=['GET', 'POST'])
    def admin_admin_create():
        """Создание нового администратора"""
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        current_admin = Admin.query.get(session['admin_id'])
        if not current_admin:
            return redirect(url_for('admin_login'))
        
        if request.method == 'GET':
            return render_template('admin/admin_form.html', title='Создание администратора', admin=current_admin, editing_admin=None)
        
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        is_superadmin = request.form.get('is_superadmin') == 'on'
        
        if not username or not password:
            return render_template('admin/admin_form.html', title='Создание администратора', admin=current_admin, editing_admin=None,
                                 error='Логин и пароль обязательны')
        
        existing = Admin.query.filter_by(username=username).first()
        if existing:
            return render_template('admin/admin_form.html', title='Создание администратора', admin=current_admin, editing_admin=None,
                                 error='Администратор с таким логином уже существует')
        
        new_admin = Admin(
            username=username,
            password_hash=generate_password_hash(password),
            email=email,
            is_superadmin=is_superadmin
        )
        
        db.session.add(new_admin)
        db.session.commit()
        
        flash('Администратор успешно создан!', 'success')
        return redirect(url_for('admin_admins'))
    
    @app.route('/admin/admins/edit/<int:admin_id>', methods=['GET', 'POST'])
    def admin_admin_edit(admin_id):
        """Редактирование администратора"""
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        current_admin = Admin.query.get(session['admin_id'])
        if not current_admin:
            return redirect(url_for('admin_login'))
        
        editing_admin = Admin.query.get_or_404(admin_id)
        
        # Нельзя редактировать самого себя через эту форму (для этого есть профиль)
        if editing_admin.id == current_admin.id:
            flash('Для редактирования своего профиля используйте соответствующую страницу', 'warning')
            return redirect(url_for('admin_dashboard'))
        
        if request.method == 'GET':
            return render_template('admin/admin_form.html', title='Редактирование администратора', admin=current_admin, editing_admin=editing_admin)
        
        username = request.form.get('username')
        email = request.form.get('email')
        is_superadmin = request.form.get('is_superadmin') == 'on'
        password = request.form.get('password')
        
        if not username:
            return render_template('admin/admin_form.html', title='Редактирование администратора', admin=current_admin, editing_admin=editing_admin,
                                 error='Логин обязателен')
        
        # Проверка уникальности логина (исключая текущего админа)
        existing = Admin.query.filter_by(username=username).first()
        if existing and existing.id != admin_id:
            return render_template('admin/admin_form.html', title='Редактирование администратора', admin=current_admin, editing_admin=editing_admin,
                                 error='Администратор с таким логином уже существует')
        
        editing_admin.username = username
        editing_admin.email = email
        editing_admin.is_superadmin = is_superadmin
        if password:
            editing_admin.password_hash = generate_password_hash(password)
        
        db.session.commit()
        
        flash('Администратор успешно обновлен!', 'success')
        return redirect(url_for('admin_admins'))
    
    @app.route('/admin/admins/delete/<int:admin_id>', methods=['POST'])
    def admin_admin_delete(admin_id):
        """Удаление администратора"""
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        current_admin = Admin.query.get(session['admin_id'])
        if not current_admin:
            return redirect(url_for('admin_login'))
        
        deleting_admin = Admin.query.get_or_404(admin_id)
        
        # Нельзя удалить самого себя
        if deleting_admin.id == current_admin.id:
            flash('Нельзя удалить самого себя!', 'error')
            return redirect(url_for('admin_admins'))
        
        db.session.delete(deleting_admin)
        db.session.commit()
        
        flash('Администратор успешно удален!', 'success')
        return redirect(url_for('admin_admins'))
    
    # ==================== API эндпоинты для автообновления ====================
    
    @app.route('/admin/api/users')
    def admin_api_users():
        """API для получения списка пользователей (JSON)"""
        if 'admin_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        users = User.query.order_by(User.registered_at.desc()).all()
        result = []
        for user in users:
            result.append({
                'id': user.id,
                'telegram_id': user.telegram_id or '-',
                'name': f"{user.first_name or ''} {user.last_name or ''}".strip(),
                'login': user.login or '-',
                'email': user.email or '-',
                'phone': user.phone or '-',
                'registered_at': user.registered_at.strftime('%d.%m.%Y %H:%M') if user.registered_at else '-',
                'profile_completed': user.profile_completed
            })
        return jsonify(result)
    
    @app.route('/admin/api/stats')
    def admin_api_stats():
        """API для получения статистики (JSON)"""
        if 'admin_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        stats = {
            'total_users': User.query.count(),
            'total_contents': Content.query.count(),
            'total_admins': Admin.query.count(),
            'total_photos': Content.query.filter_by(type='photo').count(),
            'total_videos': Content.query.filter_by(type='video').count(),
            'total_links': Content.query.filter_by(type='link').count()
        }
        return jsonify(stats)
    
    @app.route('/admin/api/contents')
    def admin_api_contents():
        """API для получения списка контента (JSON)"""
        if 'admin_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        contents = Content.query.order_by(Content.created_at.desc()).limit(50).all()
        result = []
        for content in contents:
            result.append({
                'id': content.id,
                'user': content.user.first_name if content.user else '-',
                'type': content.type,
                'content': content.content[:50] + '...' if content.content and len(content.content) > 50 else (content.content or '-'),
                'created_at': content.created_at.strftime('%d.%m.%Y %H:%M') if content.created_at else '-'
            })
        return jsonify(result)
