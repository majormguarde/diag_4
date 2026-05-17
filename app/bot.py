import os
import random
import threading
import re
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)
from app import db
from app.models import User, Content
from config import Config

_flask_app = None
_bot_app = None
_bot_thread = None

# Состояния для формы регистрации
FORM_LAST_NAME, FORM_PHONE, FORM_EMAIL, FORM_LOGIN, FORM_PASSWORD, MAIN_MENU = range(6)

def get_registration_keyboard():
    """Клавиатура для запроса фамилии"""
    return ReplyKeyboardMarkup([['Пропустить']], resize_keyboard=True)

def get_phone_keyboard():
    """Клавиатура с кнопкой отправки контакта"""
    return ReplyKeyboardMarkup([
        [{'text': '📱 Отправить номер телефона', 'request_contact': True}],
        ['Пропустить']
    ], resize_keyboard=True)

def get_skip_keyboard():
    """Простая клавиатура с кнопкой пропуска"""
    return ReplyKeyboardMarkup([['Пропустить']], resize_keyboard=True)

def get_main_menu_keyboard():
    """Главное меню после регистрации"""
    return ReplyKeyboardMarkup([
        ['Профиль', 'Заявки', 'Отчеты'],
        ['Помощь', 'Пример отчета', 'Пример диаграммы'],
        ['Выход']
    ], resize_keyboard=True)

def get_bot_app():
    global _bot_app
    if _bot_app is None:
        token = Config.TELEGRAM_BOT_TOKEN
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN не установлен в переменных окружения")
        
        _bot_app = Application.builder().token(token).build()
        
        # Обработчик для формы регистрации (ConversationHandler) - ДОЛЖЕН БЫТЬ ПЕРВЫМ!
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler('start', start_command),  # /start запускает форму для новых пользователей
                MessageHandler(filters.Regex('^Заполнить анкету$'), start_registration)
            ],
            states={
                FORM_LAST_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_last_name)
                ],
                FORM_PHONE: [
                    MessageHandler(filters.CONTACT, receive_phone),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_phone)
                ],
                FORM_EMAIL: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_email)
                ],
                FORM_LOGIN: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_login)
                ],
                FORM_PASSWORD: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_password)
                ],
                MAIN_MENU: [
                    MessageHandler(filters.Regex('^Профиль$'), handle_profile),
                    MessageHandler(filters.Regex('^Заявки$'), handle_requests),
                    MessageHandler(filters.Regex('^Отчеты$'), handle_reports),
                    MessageHandler(filters.Regex('^Помощь$'), handle_help),
                    MessageHandler(filters.Regex('^Пример отчета$'), handle_example_report),
                    MessageHandler(filters.Regex('^Пример диаграммы$'), handle_example_diagram),
                    MessageHandler(filters.Regex('^Выход$'), stop_command)
                ]
            },
            fallbacks=[
                CommandHandler('cancel', cancel_registration),
                CommandHandler('start', start_command)  # Для пользователей с завершенным профилем
            ]
        )
        _bot_app.add_handler(conv_handler)
        
        # Обработчики для уже зарегистрированных пользователей
        _bot_app.add_handler(CommandHandler("stop", stop_command))
        _bot_app.add_handler(CommandHandler("menu", menu_command))
        _bot_app.add_handler(CommandHandler("random", random_content))
        _bot_app.add_handler(CommandHandler("myid", my_id_command))
        _bot_app.add_handler(MessageHandler(filters.Regex('^Профиль$'), handle_profile))
        _bot_app.add_handler(MessageHandler(filters.Regex('^Заявки$'), handle_requests))
        _bot_app.add_handler(MessageHandler(filters.Regex('^Отчеты$'), handle_reports))
        _bot_app.add_handler(MessageHandler(filters.Regex('^Пример отчета$'), handle_example_report))
        _bot_app.add_handler(MessageHandler(filters.Regex('^Пример диаграммы$'), handle_example_diagram))
        _bot_app.add_handler(MessageHandler(filters.Regex('^Помощь$'), handle_help))
        _bot_app.add_handler(MessageHandler(filters.Regex('^Выход$'), stop_command))
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
            # Создаем нового пользователя
            db_user = User(telegram_id=telegram_id, username=username, first_name=first_name)
            db.session.add(db_user)
            db.session.commit()
            
            # Сразу начинаем заполнение анкеты
            context.user_data['telegram_id'] = telegram_id
            
            await update.message.reply_text(
                f"Добро пожаловать, {first_name}! Вы зарегистрированы.\n\n"
                "Давайте заполним ваши персональные данные.\n\n"
                "Шаг 1 из 5: Введите вашу фамилию.\n"
                "Или нажмите 'Пропустить', чтобы перейти к следующему полю.",
                reply_markup=get_registration_keyboard()
            )
            return FORM_LAST_NAME
        else:
            if not db_user.profile_completed:
                # Сразу начинаем заполнение анкеты
                context.user_data['telegram_id'] = telegram_id
                
                await update.message.reply_text(
                    f"{first_name}, давайте заполним ваши персональные данные.\n\n"
                    "Шаг 1 из 5: Введите вашу фамилию.\n"
                    "Или нажмите 'Пропустить', чтобы перейти к следующему полю.",
                    reply_markup=get_registration_keyboard()
                )
                return FORM_LAST_NAME
            else:
                # Пользователь с завершенным профилем - показываем меню
                context.user_data['telegram_id'] = telegram_id
                await update.message.reply_text(
                    f"С возвращением, {first_name}! Главное меню:",
                    reply_markup=get_main_menu_keyboard()
                )
                return MAIN_MENU

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /menu для отображения главного меню"""
    with _flask_app.app_context():
        telegram_id = update.effective_user.id
        db_user = User.query.filter_by(telegram_id=telegram_id).first()
        
        if db_user and db_user.profile_completed:
            context.user_data['telegram_id'] = telegram_id
            await update.message.reply_text(
                "Главное меню:",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await update.message.reply_text(
                "Сначала завершите регистрацию через /start",
                reply_markup=get_registration_keyboard()
            )


# Функции для обработки формы регистрации
async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало заполнения анкеты"""
    # Отладочная информация
    print(f"start_registration вызван! Текст: {update.message.text}")
    
    user = update.effective_user
    
    # Сохраняем telegram_id в context.user_data
    context.user_data['telegram_id'] = user.id
    
    await update.message.reply_text(
        f"{user.first_name}, давайте заполним ваши персональные данные.\n\n"
        "Шаг 1 из 5: Введите вашу фамилию.\n"
        "Или нажмите 'Пропустить', чтобы перейти к следующему полю.",
        reply_markup=get_registration_keyboard()
    )
    return FORM_LAST_NAME


async def receive_last_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка фамилии"""
    text = update.message.text
    
    if text == 'Пропустить':
        context.user_data['last_name'] = None
    else:
        context.user_data['last_name'] = text
    
    await update.message.reply_text(
        "Шаг 2 из 5: Введите ваш номер телефона.\n"
        "Вы можете отправить номер кнопкой ниже или ввести вручную.\n"
        "Или нажмите 'Пропустить'.",
        reply_markup=get_phone_keyboard()
    )
    return FORM_PHONE


async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка номера телефона"""
    if update.message.contact:
        context.user_data['phone'] = update.message.contact.phone_number
    elif update.message.text == 'Пропустить':
        context.user_data['phone'] = None
    else:
        context.user_data['phone'] = update.message.text
    
    await update.message.reply_text(
        "Шаг 3 из 5: Введите ваш e-mail адрес.\n"
        "Или нажмите 'Пропустить'.",
        reply_markup=get_skip_keyboard()
    )
    return FORM_EMAIL


async def receive_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка e-mail"""
    text = update.message.text
    
    if text == 'Пропустить':
        context.user_data['email'] = None
    else:
        # Простая валидация e-mail
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', text):
            await update.message.reply_text(
                "Пожалуйста, введите корректный e-mail адрес.\n"
                "Или нажмите 'Пропустить'.",
                reply_markup=get_skip_keyboard()
            )
            return FORM_EMAIL
        context.user_data['email'] = text
    
    await update.message.reply_text(
        "Шаг 4 из 5: Придумайте логин для входа в личный кабинет.\n"
        "Или нажмите 'Пропустить'.",
        reply_markup=get_skip_keyboard()
    )
    return FORM_LOGIN


async def receive_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка логина"""
    text = update.message.text
    
    if text == 'Пропустить':
        context.user_data['login'] = None
    else:
        # Простая валидация логина
        if not re.match(r'^[\w]{3,20}$', text):
            await update.message.reply_text(
                "Логин должен содержать от 3 до 20 символов (буквы, цифры, подчеркивание).\n"
                "Попробуйте другой логин или нажмите 'Пропустить'.",
                reply_markup=get_skip_keyboard()
            )
            return FORM_LOGIN
        context.user_data['login'] = text
    
    await update.message.reply_text(
        "Шаг 5 из 5: Придумайте пароль для входа в личный кабинет.\n"
        "Пароль должен содержать не менее 6 символов.\n"
        "Или нажмите 'Пропустить'.",
        reply_markup=get_skip_keyboard()
    )
    return FORM_PASSWORD


async def receive_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка пароля и завершение регистрации"""
    text = update.message.text
    
    if text == 'Пропустить':
        context.user_data['password'] = None
    else:
        if len(text) < 6:
            await update.message.reply_text(
                "Пароль должен содержать не менее 6 символов.\n"
                "Попробуйте другой пароль или нажмите 'Пропустить'.",
                reply_markup=get_skip_keyboard()
            )
            return FORM_PASSWORD
        context.user_data['password'] = text
    
    # Сохраняем данные в базу
    with _flask_app.app_context():
        telegram_id = context.user_data.get('telegram_id')
        user = User.query.filter_by(telegram_id=telegram_id).first()
        
        if user:
            # Обновляем данные пользователя
            if context.user_data.get('last_name'):
                user.last_name = context.user_data['last_name']
            if context.user_data.get('phone'):
                user.phone = context.user_data['phone']
            if context.user_data.get('email'):
                user.email = context.user_data['email']
            if context.user_data.get('login'):
                user.login = context.user_data['login']
            if context.user_data.get('password'):
                from werkzeug.security import generate_password_hash
                user.password_hash = generate_password_hash(context.user_data['password'])
            
            user.profile_completed = True
            db.session.commit()
    
    # Очищаем user_data
    context.user_data.clear()
    
    await update.message.reply_text(
        "✅ Регистрация завершена! Ваши данные сохранены.\n\n"
        "Теперь вы можете использовать все функции бота.\n"
        "Выберите раздел в меню:",
        reply_markup=get_main_menu_keyboard()
    )
    return MAIN_MENU


async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена регистрации"""
    context.user_data.clear()
    await update.message.reply_text(
        "Регистрация отменена. Вы можете начать заполнение анкеты в любое время через /start.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def handle_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки Профиль"""
    with _flask_app.app_context():
        telegram_id = update.effective_user.id
        user = User.query.filter_by(telegram_id=telegram_id).first()
        if user:
            await update.message.reply_text(
                f"📋 Ваш профиль:\n"
                f"👤 Имя: {user.first_name or 'Не указано'}\n"
                f"📝 Фамилия: {user.last_name or 'Не указано'}\n"
                f"📧 E-mail: {user.email or 'Не указано'}\n"
                f"📱 Телефон: {user.phone or 'Не указано'}\n"
                f"🔑 Логин: {user.login or 'Не указано'}"
            )
        else:
            await update.message.reply_text("Пользователь не найден. Пройдите регистрацию через /start")

async def handle_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки Заявки"""
    await update.message.reply_text(
        "📝 Раздел 'Заявки' в разработке.\n"
        "Здесь вы сможете создавать и просматривать заявки."
    )

async def handle_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки Отчеты"""
    await update.message.reply_text(
        "📊 Раздел 'Отчеты' в разработке.\n"
        "Здесь вы сможете просматривать отчеты."
    )

async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки Помощь"""
    import os
    
    # Пытаемся прочитать содержимое MANUAL.md
    manual_text = None
    manual_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'MANUAL.md')
    
    try:
        if os.path.exists(manual_path):
            with open(manual_path, 'r', encoding='utf-8') as f:
                manual_text = f.read()
    except Exception:
        manual_text = None
    
    if manual_text:
        # Форматируем текст для Telegram (убираем markdown заголовки)
        help_text = manual_text.replace('# ', '').replace('## ', '📌 ').replace('### ', '• ')
        await update.message.reply_text(help_text)
    else:
        # Резервный вариант, если файл не найден
        await update.message.reply_text(
            "❓ Помощь:\n\n"
            "Кнопки меню:\n"
            "  Профиль - ваши данные\n"
            "  Заявки - раздел в разработке\n"
            "  Отчеты - раздел в разработке\n"
            "  Помощь - эта справка\n"
            "  Выход - выйти из бота\n\n"
            "Команды:\n"
            "  /start - начать регистрацию / главное меню\n"
            "  /stop - остановить бота\n"
            "  /menu - показать меню\n"
            "  /random - случайный контент\n"
            "  /myid - узнать Telegram ID\n\n"
            "Вы можете отправлять текст, фото и видео - они будут сохранены.\n"
            "Для технической поддержки свяжитесь с администратором."
        )

async def handle_example_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки Пример отчета - отправка файла отчета"""
    import os
    
    examples_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_examples')
    report_path = os.path.join(examples_dir, 'report1.pdf')
    
    if os.path.exists(report_path):
        await update.message.reply_document(
            document=open(report_path, 'rb'),
            filename='report1.pdf',
            caption='📄 Пример диагностического отчета'
        )
    else:
        await update.message.reply_text('❌ Файл отчета не найден')

async def handle_example_diagram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки Пример диаграммы - отправка файла диаграммы"""
    import os
    
    examples_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_examples')
    diagram_path = os.path.join(examples_dir, '1.png')
    
    if os.path.exists(diagram_path):
        await update.message.reply_photo(
            photo=open(diagram_path, 'rb'),
            caption='📊 Пример диаграммы поиска неисправностей'
        )
    else:
        await update.message.reply_text('❌ Файл диаграммы не найден')

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stop для выхода из бота"""
    context.user_data.clear()
    await update.message.reply_text(
        "Бот остановлен. Вы можете запустить его снова командой /start.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

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

def is_user_in_registration(context):
    """Проверяет, находится ли пользователь в процессе регистрации"""
    return context.user_data and 'telegram_id' in context.user_data

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Пропускаем сообщения от пользователей, которые в процессе регистрации
    if is_user_in_registration(context):
        return
    
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
    # Пропускаем сообщения от пользователей, которые в процессе регистрации
    if is_user_in_registration(context):
        return
    
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
    # Пропускаем сообщения от пользователей, которые в процессе регистрации
    if is_user_in_registration(context):
        return
    
    with _flask_app.app_context():
        telegram_id = update.effective_user.id
        user = User.query.filter_by(telegram_id=telegram_id).first()
        if not user:
            await update.message.reply_text("Zарегистрируйтесь через /start")
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
    import os
    import signal
    
    # Создаем файл с PID текущего процесса в корневой директории проекта
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pid_file = os.path.join(project_dir, 'bot.pid')
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))
    
    app = get_bot_app()
    app.run_polling()
    
    # Удаляем файл PID при завершении
    try:
        os.remove(pid_file)
    except:
        pass

def run_bot_thread(flask_app):
    global _flask_app, _bot_thread
    _flask_app = flask_app
    if _bot_thread is None or not _bot_thread.is_alive():
        _bot_thread = threading.Thread(target=start_polling, daemon=True)
        _bot_thread.start()