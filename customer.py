import telebot
import sqlite3

bot = telebot.TeleBot('6877232223:AAEMwD963N3Bq1yBzEHSNlhDwvHlGd__s1Y')
name = None


@bot.message_handler(commands=['start'])
def start(message):
    conn = sqlite3.connect('с_users.sql')
    cur = conn.cursor()

    cur.execute('CREATE TABLE IF NOT EXISTS с_users (id int auto_increment primary key, c_tg_id varchar(255), c_name varchar(255), c_img varchar(255), c_info varchar(255), c_rating float(24), c_tags varchar(255))')
    conn.commit()
    cur.close()
    conn.close()

    bot.send_message(message.chat.id, f'Здравствуйте. Давайте зарегистрируем вашу сеть в нашей базе. \n'
                                      f'Начнём с простого. Как Вы называетесь?')
    bot.register_next_step_handler(message, с_user_name)


def с_user_name(message):
    """ функция считывает имя User

    :param message:
    :return:
    """
    global name
    try:
        name = message.text.strip()
        bot.send_message(message.chat.id, 'Отлично! Пришлите логотип вашей сети магазинов.')
        bot.register_next_step_handler(message, с_user_img)
    except Exception as txt_exp:
        bot.reply_to(message, 'Отправьте название вашей сети текстом.')
        bot.register_next_step_handler(message, с_user_name)


# def с_user_img(message):
#     """ функция считывает картинку User
#
#     :param message:
#     :return:
#     """
#     global photo
#     try:
#         print(message)
#         file_info = bot.get_file(message.document.file_id)
#         downloaded_file = bot.download_file(file_info.file_path)
#
#         photo = 'C:/Users/artem/tg_bot/PycharmProjects/pythonProject2/emblem/' + message.document.file_name
#         with open(photo, 'wb') as new_file:
#             new_file.write(downloaded_file)
#
#         bot.reply_to(message, "Дайте денег.")
#         bot.register_next_step_handler(message, с_user_tags)
#     except Exception as photo_ex:
#         print(photo_ex)
#         bot.reply_to(message, 'Отправьте пожалуйста картинку с соответствующим расширением.')
#         bot.register_next_step_handler(message, с_user_img)


def с_user_tags(message):
    """ функция считывает картинку User

    :param message:
    :return:
    """
    global tags
    tags = bot.get_user_profile_photos(message.chat.id)


bot.infinity_polling()