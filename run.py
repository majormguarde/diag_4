from app import create_app

app = create_app()

if __name__ == '__main__':
    # ВАЖНО: при DEBUG=True бот может запуститься дважды. Для разработки используйте debug=False
    app.run(debug=False, host='0.0.0.0', port=5000)