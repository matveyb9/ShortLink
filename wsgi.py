from app import app, init_connection_pool, init_db

if __name__ == "__main__":
    init_connection_pool()
    init_db()
    app.run()