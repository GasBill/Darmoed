import telebot
from telebot import types
import sqlite3
from common import *

bot = telebot.TeleBot('6743198990:AAGhvQw3MCVWEn97bQf0eikBvdtRhp5acQI')
name = None
user_info = dict()
is_reg = False
active_session = False
board_info = list()
page = 1
tags_map = ['Фаст-фуд', 'Русская кухня', 'Турецкая кухня',
            'Индийская кухня', 'Японская кухня', 'Французская кухня',
            'Английская кухня', 'Итальянская кухня', 'Китайская кухня', 'Кавказская  кухня']

tags_cust = ['Оценка_блюда', 'Фото_помещения', 'Фото_блюда',
             'Проверка_оборудования', 'Общая_оценка']
geo_map = ['Москва', 'Саров']
board_msgs = list()
my_orders = None
id_order = ''
def check_reg(message):
    global is_reg
    global user_info
    global active_session
    if not is_reg:
        conn = sqlite3.connect('tg_bot.db')
        cur = conn.cursor()
        cur.execute('SELECT * FROM w_users WHERE tg_id==%s' % (int(message.from_user.id)))
        info = cur.fetchall()
        is_reg = bool(info)
        if is_reg:
            print(message.from_user.id)
            info = info[0]
            user_info = {
                'name': info[0],
                'age': info[1],
                'geo': info[2],
                'rating': info[3],
                'tags': info[4]
            }
            print(user_info)
        cur.close()
        conn.close()
    active_session = True
    return is_reg


def check_my_orders(user_id) -> int:
    global my_orders
    if my_orders is None:
        conn = sqlite3.connect('tg_bot.db')
        cur = conn.cursor()
        cur.execute('SELECT id FROM orders WHERE status == \'in_progress\' & worker_id == \'%s\'' % (user_info['name']))
        my_orders = [i[0] for i in cur.fetchall()]
        print(my_orders)
        cur.close()
        conn.close()

    return len(my_orders)



def del_msg(message=None):
    global board_msgs
    try:
        if message:
            obj = message.chat.id
            for msg_id in board_msgs:
                bot.delete_message(obj, msg_id)
            board_msgs = list()
    except Exception as e:
        print(e)




@bot.message_handler(commands=['help'])
def helping(message):
    if not check_reg(message):
        registration(message)
    markup = types.ReplyKeyboardMarkup()
    btn1 = types.KeyboardButton('/status')
    btn2 = types.KeyboardButton('/my_board')
    markup.row(btn1, btn2)
    btn3 = types.KeyboardButton('/board')
    btn4 = types.KeyboardButton('/hot_board')
    markup.row(btn3, btn4)
    btn5 = types.KeyboardButton('/main')
    markup.row(btn5)
    bot.send_message(message.chat.id, f'/status - выводит Ваши данные; \n'
                     f'/main - возвращает Вас в главное меню; \n'
                     f'/my_board - показывает объявления по рекомендациям; \n'
                     f'/tasks - показывает объявления, которые Вы приняли (максимум 5); \n'
                     f'/hot_board - показывает 5 самых "горящих" объявлений в Вашем городе; \n'
                     f'/help - список всех возможностей бота. \n'
                     f''
                     f''
                     f''
                     f'', reply_markup=markup)




@bot.message_handler(commands=['main'])
def main(message):
    if not check_reg(message):
        registration(message)
    main_thread(message)





@bot.message_handler(commands=['hot_board'])
def hot_board(message):
    make_board(message)


@bot.message_handler(commands=['my_board'])
def my_board(message):
    make_board(message, is_mb=True)


def make_board(message, is_mb: bool = False):
    if not check_reg(message):
        registration(message)
    del_msg(message)
    global board_info
    global user_info
    global board_msgs
    global page
    if not board_info:
        conn = sqlite3.connect('tg_bot.db')
        cur = conn.cursor()
        cur.execute('SELECT * FROM orders WHERE status == \'open\' AND geo == \'%s\' ORDER BY end_date'% (user_info['geo']))
        board_info = cur.fetchall()
        print(board_info)
        print(user_info['geo'])
        cur.close()
        conn.close()

        if is_mb:
            user_tags = user_info['tags'].split(', ')
            def cross(tags: list) -> int:
                return len([tag for tag in tags if tag in user_tags])
            board_info = [list(row)+[cross(row[4].split(', '))] for row in board_info]
            board_info = sorted(board_info, key=lambda x: x[-1] / len(x[4].split(', ')), reverse=True)
            board_info = sorted(board_info, key=lambda x: x[-1], reverse=True)

    counter = 3 * (page - 1)
    for i in range(3 * (page - 1), min(page * 3, len(board_info)) - 1):
        counter += 1
        row = board_info[i]
        adv = row_to_msg(row)
        markup = types.InlineKeyboardMarkup()
        a = types.InlineKeyboardButton('Принять', callback_data=f'accept {row[0]}')
        markup.row(a)
        msg = bot.send_photo(message.chat.id, open(f'.{row[7]}', 'rb'),
                             caption=adv, reply_markup=markup)
        board_msgs.append(msg.id)

    row = board_info[counter]
    adv = row_to_msg(row)
    markup = types.InlineKeyboardMarkup()
    a = types.InlineKeyboardButton('Принять', callback_data=f'accept {row[0]}')
    markup.row(a)
    if page != 1:
        b = types.InlineKeyboardButton('^', callback_data='prev_page')
        markup.row(b)
    if counter != len(board_info) - 1:
        c = types.InlineKeyboardButton('v', callback_data='next_page')
        markup.row(c)
    msg = (bot.send_photo(message.chat.id, open(f'.{row[7]}', 'rb'), caption=adv, reply_markup=markup))
    board_msgs.append(msg.id)


def row_to_msg(row: list) -> str:
    tags_w = row[4].split(', ')
    tag_m = ''.join([f'• {tags_map[int(tag)]}\n' for tag in tags_w])
    tags_c = row[5].split(', ')
    tag_mc = ' '.join([f'#{tags_cust[int(tag)]}' for tag in tags_c])
    date = str(row[8])
    date = date[4:] + '.' + date[2: 4] + '.' + date[:2]
    return f'{row[2]}\n\nГород: {geo_map[int(row[3]) - 1]}\n\nСпециализация:\n{tag_m}\nТребования:\n{tag_mc}\nДата истечения срока запроса: {date}'




@bot.message_handler(commands=['start'])
def start(message):
    global user_info

    if check_reg(message):
        reg_d_user(message)
    else:
        registration(message)

    if message.from_user.is_bot:
        bot.send_message(message.chat.id, 'I hate you, brother.')
        bot.register_next_step_handler(message, w_silent)


def w_silent():
    print("user is my enemy")


def registration(message):
    global user_info
    user_info['name'] = int(message.from_user.id)
    global user_name
    user_name = message.from_user.username
    print(user_name)
    bot.send_message(message.chat.id, 'Здравствуйте. Давайте зарегистрируем Вас в нашей базе.')
    bot.send_message(message.chat.id,
                     f'Буду к Вам обращаться {user_name}. Подскажите, пожалуйста, Ваш возраст.')
    bot.register_next_step_handler(message, w_user_age)


def w_user_age(message):
    try:
        user_info['age'] = int(message.text.strip())
        if user_info['age'] > 0:
            markup = types.ReplyKeyboardMarkup()
            btn1 = types.KeyboardButton('Москва')
            btn2 = types.KeyboardButton('Саров')
            markup.row(btn1, btn2)
            bot.send_message(message.chat.id, 'Отлично! В каком городе вы проживаете? Укажите вариант из предложенных.', reply_markup=markup)
            bot.register_next_step_handler(message, w_user_geo)
    except Exception as e:
        print(e)
        bot.reply_to(message, 'Отправьте ваш возраст числом. Или более нуля.')
        bot.register_next_step_handler(message, w_user_age)


def w_user_geo(message):
    try:
        geo = message.text.strip()
        if geo == 'Москва' or geo == 'Саров':
            if geo == 'Москва':
                user_info['geo'] = '1'
            else:
                user_info['geo'] = '2'
            w_user_tags(message)
        else:
            bot.reply_to(message, 'К сожалению наша сеть пока не работает в вашем городе.')
            bot.register_next_step_handler(message, w_user_geo)
    except Exception as e:
        print(e)


def w_user_tags(message):
    user_info['tags'] = set()
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Фаст-фуд', callback_data='ff')
    btn2 = types.InlineKeyboardButton('Русская кухня', callback_data='tay')
    markup.row(btn1, btn2)
    btn3 = types.InlineKeyboardButton('Турецкая кухня', callback_data='tur')
    btn4 = types.InlineKeyboardButton('Индийская кухня', callback_data='ind')
    markup.row(btn3, btn4)
    btn5 = types.InlineKeyboardButton('Японская кухня', callback_data='ipon')
    btn6 = types.InlineKeyboardButton('Французская кухня', callback_data='fran')
    markup.row(btn5, btn6)
    btn7 = types.InlineKeyboardButton('Английская кухня', callback_data='isp')
    btn8 = types.InlineKeyboardButton('Итальянская кухня', callback_data='ital')
    markup.row(btn7, btn8)
    btn9 = types.InlineKeyboardButton('Китайская кухня', callback_data='kit')
    btn10 = types.InlineKeyboardButton('Кавказская кухня', callback_data='mex')
    markup.row(btn9, btn10)
    btn11 = types.InlineKeyboardButton('ГОТОВО', callback_data='w_reg_end')
    markup.row(btn11)
    bot.send_message(message.chat.id, 'Каковы Ваши предпочтения?', reply_markup=markup)


def reg_d_user(message):
    bot.send_message(message.chat.id,
                     f'Вы зарегистрированны! \n'
                     f'Ознакомьтесь, пожалуйста, с возможностями бота, использовав команду /help.')
    main_thread(message)


def main_thread(message):
    markup = types.ReplyKeyboardMarkup()
    btn1 = types.KeyboardButton('/status')
    btn2 = types.KeyboardButton('/my_board')
    markup.row(btn1, btn2)
    btn3 = types.KeyboardButton('/board')
    btn4 = types.KeyboardButton('/hot_board')
    markup.row(btn3, btn4)
    btn5 = types.KeyboardButton('/help')
    markup.row(btn5)
    bot.send_message(message.chat.id, 'Вы в главном меню.', reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: True)
def ask_reg(callback):
    """
    Составление Ask сообщения
    :param callback:
    :return:
    """
    global active_session
    if not active_session:
        return
    global tags_map
    w_reg_end = False
    retry_end_reg = False
    if callback.data == 'w_reg_end' and not w_reg_end:
        if user_info['tags']:
            w_reg_end = True
            print(w_reg_end)
            markup = types.InlineKeyboardMarkup()
            mes = (f'Отлично! \n'
                   f'Проверьте, Вы уверены в данных, которые Вы ввели. \n\n'
                   f'Имя: {user_name} \n\n'
                   f'Возраст: {user_info["age"]} \n\n'
                   f'Город: {geo_map[int(user_info["geo"] ) - 1]} \n\n'
                   f'Ваши предпочтения:\n')
            for i in user_info['tags']:
                tag = tags_map[int(i)]
                mes += f'• {tag} \n'
                print(mes)

            btn1 = types.InlineKeyboardButton('Закончить регистрацию', callback_data='reg_end')
            btn2 = types.InlineKeyboardButton('Начать заново', callback_data='retry_reg')
            markup.row(btn1, btn2)
            bot.send_message(callback.message.chat.id, mes, reply_markup=markup)
        else:
            bot.send_message(callback.message.chat.id, 'Выберите ваши предпочтения.')
    if callback.data == 'reg_end' and not retry_end_reg:
        retry_end_reg = True
        conn = sqlite3.connect('tg_bot.db')
        cur = conn.cursor()
        cur.execute('''INSERT INTO 
            w_users 
            (tg_id, 
            age, 
            geo, 
            rating, 
            tags) 
            VALUES 
            ('%s', '%s', '%s', '%s', '%s')''' % (user_info['name'], user_info['age'], user_info['geo'], 4, ', '.join(user_info['tags'])))
        conn.commit()

        cur.execute('SELECT * FROM w_users')
        w_users = cur.fetchall()
        print(w_users)
        cur.close()
        conn.close()
        reg_d_user(callback.message)

        if callback.data == 'retry_reg' and not retry_end_reg:
            retry_end_reg = True
            bot.send_message(callback.message.chat.id, 'Хорошо, давайте начнём с начала.')
            bot.send_message(callback.message.chat.id, 'Подскажите, пожалуйста, Ваш возраст.')
            bot.register_next_step_handler(callback.message, w_user_age)


    """
    Tags
    :param callback:
    :return:
    """
    if callback.data == 'ff':
        user_info['tags'].add('0')
    elif callback.data == 'tay':
        user_info['tags'].add('1')
    elif callback.data == 'tur':
        user_info['tags'].add('2')
    elif callback.data == 'ind':
        user_info['tags'].add('3')
    elif callback.data == 'ipon':
        user_info['tags'].add('4')
    elif callback.data == 'fran':
        user_info['tags'].add('5')
    elif callback.data == 'isp':
        user_info['tags'].add('6')
    elif callback.data == 'ital':
        user_info['tags'].add('7')
    elif callback.data == 'kit':
        user_info['tags'].add('8')
    elif callback.data == 'mex':
        user_info['tags'].add('9')

    global page

    if callback.data == 'prev_page':
        del_msg(callback.message)
        page -= 1
        make_board(callback.message)
    elif callback.data == 'next_page':
        del_msg(callback.message)
        page += 1
        make_board(callback.message)

    global id_order

    if callback.data.split(' ')[0] == 'accept':
        id_order = callback.data.split(' ')[1]
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('Да', callback_data=f'yes_accept')
        btn2 = types.InlineKeyboardButton('Нет', callback_data=f'no_accept')
        markup.row(btn1, btn2)
        bot.send_message(callback.message.chat.id,'Вы уверены в вашем выборе?', reply_markup=markup)

    global my_orders
    global board_info

    if callback.data == 'yes_accept':
        if check_my_orders(user_info['name']) < 3:
            conn = sqlite3.connect('tg_bot.db')
            cur = conn.cursor()
            cur.execute('''UPDATE orders 
                        SET status = \'%s\', worker_id = \'%s\'
                        WHERE id == %s 
                        ''' % ('in_progress', user_info['name'], id_order))
            conn.commit()
            cur.close()
            conn.close()
            board_info = list()
            my_orders.append(id_order)
            bot.send_message(callback.message.chat.id, 'Вы успешно взяли заказ в работу.')
            del_msg(callback.message)
            main_thread(callback.message)
        else:
            bot.send_message(callback.message.chat.id, 'Вы не можете принять заказ, колличество заказов достигло максимума(3).')
    elif callback.data == 'no_accept':
        bot.delete_message(callback.message.chat.id, callback.message.id)



bot.infinity_polling()
