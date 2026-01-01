import telebot
from telebot import types
import os
from dotenv import load_dotenv
from bot.database.models import init_db
from bot.database.crud import add_user, get_random_word, mark_word_as_learned, get_wrong_answers, get_wrong_translations, get_translation, add_word, get_wrong_translations_personal, add_word_users, create_word_for_users, get_remaining_words_count, get_learned_words
import random

# Инициализация бота
load_dotenv()
token = os.getenv('TOKEN')
bot = telebot.TeleBot(token)

# Состояние пользователей
user_state = {}
user_state_test={}

# ====== Клавиатуры ======

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton("Учить слова 📚"),
        types.KeyboardButton("Пройти тест 📝"),
        types.KeyboardButton("Повторить слова 🔄"),
        types.KeyboardButton("Помощь ❓")
    )
    return markup

def learn_words_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton("Добавить слово ➕"),
        types.KeyboardButton("Начать урок ▶️"),
        types.KeyboardButton("Главное меню 🏠")
    )
    return markup

def topics_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton("Еда"),
        types.KeyboardButton("Путешествия"),
        types.KeyboardButton("Работа"),
        types.KeyboardButton("Семья"),
        types.KeyboardButton("Персональное"),
        types.KeyboardButton("Главное меню 🏠")
    )
    return markup

def number_of_words_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton("5"),
        types.KeyboardButton("15"),
        types.KeyboardButton("50")
    )
    return markup

def answer_options(topic, correct_word, user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if topic == "Персональное":
        wrong_translations = get_wrong_translations_personal(user_id, correct_word)
    else:
        wrong_translations = get_wrong_translations(topic, correct_word)
    correct_translation = get_translation(correct_word, topic, user_id)
    answers = wrong_translations + [correct_translation]
    answers = [a for a in answers if a is not None]  
    random.shuffle(answers)

    for ans in answers:
        markup.add(types.KeyboardButton(ans))

    markup.add(types.KeyboardButton("Главное меню 🏠"))
    return markup

# ===================
# ====== Старт ======

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    bot.reply_to(
        message,
        f"👋 Привет, {user_name}! Я EnglishCard — бот для изучения английских слов. Я помогу тебе:\n"
        "• учить новые слова\n• проверять знания в формате теста\n• добавлять свои слова\n"
        "Выбери действие ниже 👇",
        reply_markup=main_menu()
    )
    add_user(message.from_user.id, user_name)
    print(f"Пользователь {user_name} с ID {message.from_user.id} начал использовать бота.")
    user_state[message.from_user.id] = {
        "rounds_left": 0,
    }
    create_word_for_users(message.from_user.id)
    print(f"Созданы персональные слова для пользователя {message.from_user.id}.")
# ====== Учить слова ======

@bot.message_handler(func=lambda m: m.text == "Учить слова 📚")
def learn_words(message):
    bot.reply_to(message, "Выбери действие:", reply_markup=learn_words_keyboard())

@bot.message_handler(func=lambda m: m.text == "Добавить слово ➕")
def add_new_word(message):
    bot.send_message(message.chat.id, "Напишите слово которое хотите добавить и перевод через запятую. В данном порядке")
    # text = message.text   
    # word, trans = message.text.split(',')
    # word = word.strip()
    # trans = trans.strip()
    # print(trans)
    bot.register_next_step_handler(message, proces_word_step)

# на главное меню
@bot.message_handler(func=lambda m: m.text == "Главное меню 🏠")
def back_to_main(message):
    bot.reply_to(message, "Возвращаемся в главное меню.", reply_markup=main_menu())

# Добавление пользовательского слова
def proces_word_step(message):
    word, trans = message.text.split(',')
    if message.text == "Главное меню 🏠":
        bot.send_message(message.chat.id, "Возвращаемся в главное меню.", reply_markup=main_menu())
        return
    user_id = message.from_user.id
    word = word.strip()
    trans = trans.strip()
    add_word_users(user_id, word, trans, 'Персональное')
    print(f"Пользователь {user_id} добавил слово '{word}' с переводом '{trans}'.")
    bot.send_message(message.chat.id, f"Слово '{word}' с переводом '{trans}' добавлено в ваши персональные слова.", reply_markup=learn_words_keyboard())

# Начать урок 
@bot.message_handler(func=lambda m: m.text == "Начать урок ▶️")
def start_lesson(message):
    bot.send_message(message.chat.id, "Выбери тему для урока:", reply_markup=topics_keyboard())
    bot.register_next_step_handler(message, choose_topic)


def choose_topic(message):
    topic = message.text
    msg = bot.send_message(message.chat.id, "Сколько слов ты хочешь выучить за этот урок?", reply_markup=number_of_words_keyboard())
    bot.register_next_step_handler(msg, lambda m: choose_count(m, topic))


def choose_count(message, topic):
    try:
        rounds = int(message.text)
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, выбери число слов с клавиатуры.", reply_markup=number_of_words_keyboard())
        bot.register_next_step_handler(message, lambda m: choose_count(m, topic))
        return
    user_id = message.from_user.id
    first_word = get_random_word(topic, user_id)
    if not first_word:
        bot.send_message(message.chat.id, f"В теме '{topic}' пока нет слов. Добавь слова или выбери другую тему.", reply_markup=learn_words_keyboard())
        return
    user_state[user_id] = {
        "topic": topic,
        "rounds_left": rounds,
        "current_word": first_word
    }
    print(f"Пользователь {user_id} начал урок по теме '{topic}' на {rounds} слов {first_word}.")
    start_quiz_step(message)

# ====== Логика урока ======

def start_quiz_step(message):
    user_id = message.from_user.id
    state = user_state.get(user_id)

    if not state:
        bot.send_message(message.chat.id, "Ошибка состояния. Начни урок заново.", reply_markup=main_menu())
        return

    if state["rounds_left"] <= 0:
        bot.send_message(message.chat.id, "Урок завершен! 🎉", reply_markup=main_menu())
        del user_state[user_id]
        return

    word = state["current_word"]
    bot.send_message(
        message.chat.id,
        f"Как переводится слово '{word}'?",
        reply_markup=answer_options(state["topic"], word, user_id)

    )
    bot.register_next_step_handler(message, check_answer)

def check_answer(message):
    user_id = message.from_user.id
    state = user_state.get(user_id)

    if not state:
        bot.send_message(message.chat.id, "Ошибка состояния. Начни урок заново.", reply_markup=main_menu())
        return
    if message.text == "Главное меню 🏠":
        bot.send_message(message.chat.id, "Возвращаемся в главное меню.", reply_markup=main_menu())
        del user_state[user_id]
        return
    word = state["current_word"]
    topic = state["topic"]

    if message.text == get_translation(word, topic, user_id):
        bot.send_message(message.chat.id, "Правильно! 🎉")
        mark_word_as_learned(word, topic, user_id) 

        # уменьшаем количество оставшихся слов и выбираем следующее
        state["rounds_left"] -= 1
        left_words = get_remaining_words_count(user_id, topic, False)
        if left_words < 1:
            bot.send_message(message.chat.id, f"Все слова в теме '{topic}' выучены! Выбери другую тему или добавь новые слова.", reply_markup=learn_words_keyboard())
            del user_state[user_id]
            return
        print(f"Осталось слов для изучения у пользователя {user_id} в теме '{topic}': {left_words}.")
        if state["rounds_left"] > 0:
            state["current_word"] = get_random_word(state["topic"], user_id)
            start_quiz_step(message)
        else:
            bot.send_message(message.chat.id, "Урок завершен! 🎉", reply_markup=main_menu())
            del user_state[user_id]
    else:
        bot.send_message(message.chat.id, f"Неправильно. Попробуй еще раз!")
        start_quiz_step(message)
        print(f"Пользователь {user_id} ответил неправильно на слово '{word}'. Ответ: '{message.text}'")

# ====== Пройти тест ======
@bot.message_handler(func=lambda m: m.text == "Пройти тест 📝")
def take_test(message):
    bot.send_message(message.chat.id, "Выбери тему для теста:", reply_markup=topics_keyboard())
    # left = 10
    bot.register_next_step_handler(message, choose_test)
    user_id = message.from_user.id
    topic = message.text
    correct_word = get_learned_words(user_id, topic, 10)
    user_state_test[user_id] = {
        "topic" : None,
        # "current_word" : correct_word
        "words" : [],
        "rounds" : 10,
        "correct_answ" : 0,
        "wrong_answ" : 0
    }


def choose_test(message):
    user_id = message.from_user.id
    topic = message.text
    state = user_state_test.get(user_id)
    state["topic"] = topic
    words = get_learned_words(user_id, topic, 10)
    state["words"] = words
    print(words)
    state = user_state_test.get(user_id)
    if not state:
        bot.send_message(message.chat.id, "Ошибка состояния. Начни тест заново.")
        return
    bot.send_message(message.chat.id, f"Начинаем тест по теме '{topic}'!", reply_markup=main_menu())
    # correct_word = get_learned_words(user_id, topic)
    if words == None:
        bot.send_message(message.chat.id, f"В теме '{topic}' нет выученных слов для теста. Сначала выучи слова!", reply_markup=learn_words_keyboard())
        return
    start_test(message, words, topic, user_id)
    
def start_test(message, words, topic, user_id):
    state = user_state_test.get(user_id)
    if state["rounds"] > 0:
        print(f"Выбранное слово для теста: {words[0]}")
        bot.send_message(message.chat.id, f"Как переводится слово '{words[0]}'?", reply_markup=answer_options(topic, words[0], user_id))
        bot.register_next_step_handler(message, check_test_answer, words[0], topic)
    else:
        test_finish(message)

def check_test_answer(message, word, topic):
    user_id = message.from_user.id
    state = user_state_test.get(user_id)
    words = state["words"]
    if message.text == "Главное меню 🏠":
        bot.send_message(message.chat.id, "Возвращаемся в главное меню.", reply_markup=main_menu())
        return
    if message.text == get_translation(word, topic, user_id):
        bot.send_message(message.chat.id, "Правильно! 🎉")
        print(f"Пользователь {user_id} правильно ответил на тестовое слово '{word}'.")
        state["rounds"] -= 1
        state["correct_answ"] += 1
        state["words"].pop(0)
        print(state["words"])
        # new_word = get_learned_words(user_id, topic)
        if not word:
            bot.send_message(message.chat.id, f"В теме '{topic}' нет выученных слов для теста. Сначала выучи слова!", reply_markup=learn_words_keyboard())
            return
        else:
            start_test(message, words, topic, user_id)
    else:
        bot.send_message(message.chat.id, f"Неправильно. Правильный ответ: :{get_translation(word, topic, user_id)}")
        print(f"Пользователь {user_id} неправильно ответил на тестовое слово '{word}'. Ответ: '{message.text}'")
        state["words"].pop(0)
        state["rounds"] -= 1
        state["wrong_answ"] += 1
        # new_word = get_learned_words(user_id, topic,)
        if not word:
            bot.send_message(message.chat.id, f"В теме '{topic}' нет выученных слов для теста. Сначала выучи слова!", reply_markup=learn_words_keyboard())
            return
        else:
            start_test(message, words, topic, user_id)

#  КОНЕЦ ТЕСТА
def test_finish(message):
    user_id = message.from_user.id
    state = user_state_test.get(user_id)
    grate = round(state["correct_answ"]/10 * 5)
    if grate < 2:
        grate = 2
    bot.send_message(message.chat.id, f'Поздравляю, тест пройден! Ваши результаты:\nВерных ответов:{state["correct_answ"]}/10\nОценка:{grate}', reply_markup=main_menu())


@bot.message_handler(func=lambda m: m.text == "Повторить слова 🔄")
def repeat_words(message):
    bot.send_message(message.chat.id, "Выбери тему для теста:", reply_markup=topics_keyboard())
    # user_id = message.from_user.id
    # words = get_learned_words(user_id, topic, 50)
    # print(topic)
    # print(words)
    bot.register_next_step_handler(message, get_words)


def get_words(message):
    topic = message.text
    user_id = message.from_user.id
    words = get_learned_words(user_id, topic, 50)
    print(topic)
    print(words)
    # bot.register_next_step_handler(message, create_repeat_test, words)
    create_repeat_test(message, words, topic)


def create_repeat_test(message, words, topic):
    # topic = message.text
    user_id = message.from_user.id
    # print(words)
    if not words:
        # bot.send_message(message.chat.id, f"Как переводится слово {word}?", reply_markup=answer_options(topic, word, user_id))
        # bot.register_next_step_handler(message, check_answer_rep, word, topic)
        bot.send_message(message.chat.id,"Нет слов для повторения 😔",reply_markup=main_menu())
        return
    else:
        word = words[0]
        print(word)
        bot.send_message(message.chat.id, f"Как переводится слово {word}?", reply_markup=answer_options(topic, word, user_id))
        bot.register_next_step_handler(message, check_answer_rep, word, topic, words)

def check_answer_rep(message, word, topic, words):
    # Обработка дмоой
    user_id = message.from_user.id
    if message.text == get_translation(word, topic, user_id):
        bot.send_message(message.chat.id, "Верно! Идем дальше")
        words.pop(0)
        print(words)
        create_repeat_test(message, words, topic)
    elif message.text == get_translation(word, topic, user_id):
        bot.send_message(
            message.chat.id,
            f"Неверно, верный ответ: {get_translation(word, topic, user_id)}"
        )
        words.pop(0)
        print(words)
        create_repeat_test(message, words, topic)
    elif message.text == "Главное меню 🏠":
        bot.send_message(message.chat.id, "Возвращаемся в главное меню.", reply_markup=main_menu())
        return
    else:
        bot.send_message(message.chat.id, "Вы ввели непонятные символы", reply_markup=main_menu())
        return
#

@bot.message_handler(func=lambda m: m.text == "Помощь ❓")
def help_message(message):
    bot.reply_to(message, "По вопросам и предложениям пишите сюда: @aaylbb")

# ====== Запуск бота ======

if __name__ == "__main__":
    init_db()
    print("Bot started")
    bot.polling(none_stop=True, skip_pending=True)
