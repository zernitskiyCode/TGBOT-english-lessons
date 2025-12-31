from bot.database.db import get_db_connection

# Добавление пользователя
def add_user(telegramid, user_name):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO users (tg_id, name) VALUES (%s, %s) ON CONFLICT(tg_id) DO NOTHING",
        (telegramid, user_name)
    )
    db.commit()
    cursor.close()
    db.close()

# Получение пользователя по tg_id
def get_user_by_tg_id(tg_id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT tg_id, name FROM users WHERE tg_id = %s", (tg_id,))
    user = cursor.fetchone()
    cursor.close()
    db.close()
    return user

# Получение случайного слова по теме
def get_random_word(topic, user_id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("""
        SELECT word FROM words_users
        WHERE id_user = %s AND topic = %s AND pass = false
        ORDER BY RANDOM() LIMIT 1
    """, (user_id, topic))
    row = cursor.fetchone()
    cursor.close()
    db.close()
    return row[0] if row else None

# Добавление нового слова words
def add_word(id_user, word, translation, topic):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO words (id, word, translation, topic) VALUES (%s, %s, %s, %s)",
        (id_user, word, translation, topic)
    )
    db.commit()
    cursor.close()
    db.close()

# Добавление нового слова words_users
def add_word_users(id_user, word, translation, topic):
    
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO words_users (id_user, word, translation, topic) VALUES (%s, %s, %s, %s)",
        (id_user, word, translation, topic)
    )
    db.commit()
    cursor.close()
    db.close()

# Отметить слово как выученное
def mark_word_as_learned(word, topic, user_id=None):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE words_users SET pass = TRUE
        WHERE id_user = %s AND word = %s""", (user_id, word))
    db.commit()
    cursor.close()
    db.close()


# Получение неправильных ответов на английском
def get_wrong_answers(topic, correct_word):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute(
        "SELECT word FROM words WHERE topic = %s AND word != %s ORDER BY RANDOM() LIMIT 3",
        (topic, correct_word)
    )
    words = [row[0] for row in cursor.fetchall()]
    cursor.close()
    db.close()
    return words
# Получение неправильных ответов на русском
def get_wrong_translations(topic, word):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute(
        "SELECT translation FROM words WHERE topic = %s AND word != %s ORDER BY RANDOM() LIMIT 3",
        (topic, word)
    )
    translations = [row[0] for row in cursor.fetchall()]
    cursor.close()
    db.close()
    return translations
# Получение перевода
def get_translation(word, topic, user_id):
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        SELECT translation FROM words_users
        WHERE id_user = %s AND word = %s AND topic = %s
    """, (user_id, word, topic))

    row = cursor.fetchone()
    cursor.close()
    db.close()
    return row[0] if row else None


def get_wrong_translations_personal(user_id, correct_word):
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        SELECT translation FROM words_users
        WHERE id_user = %s AND word != %s
        ORDER BY RANDOM()
        LIMIT 3
    """, (user_id, correct_word))

    translations = [row[0] for row in cursor.fetchall()]
    cursor.close()
    db.close()
    return translations

def create_word_for_users(tg_id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO words_users (id_user, word, translation, topic, pass)
        SELECT %s, word, translation, topic, FALSE
        FROM words
        WHERE word NOT IN (
            SELECT word FROM words_users WHERE id_user = %s
        )
    """, (tg_id, tg_id))
    db.commit()
    cursor.close()
    db.close()

# Получение количества оставшихся невыученных слов по теме
def get_remaining_words_count(user_id, topic, pass_rem):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("""
        SELECT COUNT(*) 
        FROM words_users 
        WHERE id_user=%s AND topic=%s AND pass=%s
    """, (user_id, topic, pass_rem))
    count = cursor.fetchone()[0]
    cursor.close()
    db.close()
    return count

# Получение случайного из выученных слов по теме дял теста
def get_learned_words(user_id, topic, limit):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("""
        SELECT word FROM words_users
        WHERE id_user=%s AND topic=%s AND pass=TRUE
        ORDER BY RANDOM() LIMIT %s
    """, (user_id, topic, limit))
    words = [row[0] for row in cursor.fetchall()]
    cursor.close()
    db.close()
    return words