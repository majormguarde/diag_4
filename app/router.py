from flask import render_template, request
from app.models import User, Content

def register_routes(app):
    @app.route('/')
    def index():
        return render_template('index.html')
    
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
        
        contents = Content.query.filter_by(user_id=user.id).order_by(Content.created_at.desc()).all()
        return render_template('cabinet.html', user=user, contents=contents)