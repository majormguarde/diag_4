from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    from app import routes, models, bot
    routes.register_routes(app)
    
    # Запускаем бота в фоновом потоке (polling)
    bot.run_bot_thread(app)
    
    return app