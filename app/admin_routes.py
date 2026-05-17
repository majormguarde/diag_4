from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User, Content, Admin

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
