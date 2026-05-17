from app import create_app

app = create_app()

# Запускаем бота в фоновом потоке (polling) - только если запуск через run.py
if __name__ == '__main__':
    from app import bot
    bot.run_bot_thread(app)
    
    # ВАЖНО: при DEBUG=True бот может запуститься дважды. Для разработки используйте debug=False
    app.run(debug=False, host='0.0.0.0', port=5000)