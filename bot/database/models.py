from bot.database.db import get_db_connection

def init_db():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS words (
        id SERIAL PRIMARY KEY,
        word VARCHAR(100) NOT NULL,
        translation VARCHAR(100) NOT NULL,
        topic VARCHAR(100) NOT NULL,
        pass BOOLEAN DEFAULT FALSE
        );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        tg_id BIGINT UNIQUE NOT NULL,
        name VARCHAR(100) NOT NULL,
        CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS words_users (
        id_user BIGINT NOT NULL REFERENCES users(tg_id),
        word VARCHAR(100) NOT NULL,
        translation VARCHAR(100) NOT NULL,
        topic VARCHAR(100) DEFAULT 'Персональное',
        pass BOOLEAN DEFAULT FALSE
);
""")

    db.commit()
    db.close()