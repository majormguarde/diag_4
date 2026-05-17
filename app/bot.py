import os
import random
import threading
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from app import db
from app.models import User, Content
from config import Config

_flask_app = None
_bot_app = None
_bot_thread = None

def get_bot_app():
    global _bot_app
    if _bot_app is None:
        token = Config.TELEGRAM_BOT_TOKEN
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN не установлен в переменных окружения")
        _bot_app = Application.builder().token(token).build()
        _bot_app.add_handler(CommandHandler("start", start_command))
        _bot_app.add_handler(CommandHandler("random", random_content))
        _bot_app.add_handler(CommandHandler("myid", my_id_command))
        _bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        _bot_app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        _bot_app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    return _bot_app

def is_url(text):
    return re.match(r'https?://\S+', text) is not None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with _flask_app.app_context():
        user = update.effective_user
        telegram_id = user.id
        username = user.username
        first_name = user.first_name
        
        db_user = User.query.filter_by(telegram_id=telegram_id).first()
        if not db_user:
            db_user = User(telegram_id=telegram_id, username=username, first_name=first_name)
            db.session.add(db_user)
            db.session.commit()
            await update.message.reply_text(
                f"Добро пожаловать, {first_name}! Вы зарегистрированы.\n"
                "Отправляйте мне текст, фото, видео или ссылки.\n"
                "Команда /random – получить случайный контент из вашего кабинета.\n"
                "Команда /myid – узнать свой Telegram ID для входа в веб-кабинет."
            )
        else:
            await update.message.reply_text(f"С возвращением, {first_name}! Используйте /random.")

async def my_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(f"Ваш Telegram ID: `{user.id}`. Используйте его для входа в веб-кабинет.", parse_mode='Markdown')

async def random_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with _flask_app.app_context():
        telegram_id = update.effective_user.id
        user = User.query.filter_by(telegram_id=telegram_id).first()
        if not user:
            await update.message.reply_text("Сначала зарегистрируйтесь через /start")
            return
        
        contents = Content.query.filter_by(user_id=user.id).all()
        if not contents:
            await update.message.reply_text("У вас пока нет контента. Отправьте что-нибудь!")
            return
        
        chosen = random.choice(contents)
        if chosen.type == 'text':
            await update.message.reply_text(chosen.content)
        elif chosen.type == 'link':
            await update.message.reply_text(f"Ссылка: {chosen.content}")
        elif chosen.type == 'photo':
            await update.message.reply_photo(photo=chosen.file_id, caption=chosen.content or "Фото")
        elif chosen.type == 'video':
            await update.message.reply_video(video=chosen.file_id, caption=chosen.content or "Видео")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with _flask_app.app_context():
        telegram_id = update.effective_user.id
        user = User.query.filter_by(telegram_id=telegram_id).first()
        if not user:
            await update.message.reply_text("Зарегистрируйтесь через /start")
            return
        
        text = update.message.text
        content_type = 'link' if is_url(text) else 'text'
        new_content = Content(user_id=user.id, type=content_type, content=text)
        db.session.add(new_content)
        db.session.commit()
        await update.message.reply_text(f"✅ {content_type.capitalize()} сохранён! Используйте /random.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with _flask_app.app_context():
        telegram_id = update.effective_user.id
        user = User.query.filter_by(telegram_id=telegram_id).first()
        if not user:
            await update.message.reply_text("Зарегистрируйтесь через /start")
            return
        
        photo = update.message.photo[-1]
        file_id = photo.file_id
        caption = update.message.caption or ""
        
        bot = context.bot
        file = await bot.get_file(file_id)
        user_folder = os.path.join(Config.UPLOAD_FOLDER, f"user_{user.id}")
        os.makedirs(user_folder, exist_ok=True)
        local_filename = f"{file_id}.jpg"
        local_path = os.path.join(user_folder, local_filename)
        await file.download_to_drive(local_path)
        relative_path = f"uploads/user_{user.id}/{local_filename}"
        
        new_content = Content(
            user_id=user.id,
            type='photo',
            content=caption,
            file_id=file_id,
            local_path=relative_path
        )
        db.session.add(new_content)
        db.session.commit()
        await update.message.reply_text("✅ Фото сохранено! Используйте /random.")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with _flask_app.app_context():
        telegram_id = update.effective_user.id
        user = User.query.filter_by(telegram_id=telegram_id).first()
        if not user:
            await update.message.reply_text("Зарегистрируйтесь через /start")
            return
        
        video = update.message.video
        file_id = video.file_id
        caption = update.message.caption or ""
        
        bot = context.bot
        file = await bot.get_file(file_id)
        user_folder = os.path.join(Config.UPLOAD_FOLDER, f"user_{user.id}")
        os.makedirs(user_folder, exist_ok=True)
        local_filename = f"{file_id}.mp4"
        local_path = os.path.join(user_folder, local_filename)
        await file.download_to_drive(local_path)
        relative_path = f"uploads/user_{user.id}/{local_filename}"
        
        new_content = Content(
            user_id=user.id,
            type='video',
            content=caption,
            file_id=file_id,
            local_path=relative_path
        )
        db.session.add(new_content)
        db.session.commit()
        await update.message.reply_text("✅ Видео сохранено! Используйте /random.")

def start_polling():
    app = get_bot_app()
    app.run_polling()

def run_bot_thread(flask_app):
    global _flask_app, _bot_thread
    _flask_app = flask_app
    if _bot_thread is None or not _bot_thread.is_alive():
        _bot_thread = threading.Thread(target=start_polling, daemon=True)
        _bot_thread.start()