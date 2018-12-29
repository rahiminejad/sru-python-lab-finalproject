# Created by abolfazl rahiminejad and fazel khorrami
import telepot
import time
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton
import sqlite3
import threading
import sys
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

token = sys.argv[1]
bot = telepot.Bot(token)
stage = {}

conn = sqlite3.connect('setting.db')  # select database file to connect
c = conn.cursor()

try:
    c.execute('SELECT * FROM users')
except sqlite3.OperationalError:
    c.execute(
        'CREATE table users ( userid VARCHAR(8) NOT NULL, status VARCHAR(8) NOT NULL DEFAULT "clean", userToChat VARCHAR(8), chatStatus VARCHAR(20) NOT NULL DEFAULT "not active", photo BOOLEAN NOT NULL DEFAULT "TRUE" );')
    conn.commit()
conn.close()


def query(query):
    conn = sqlite3.connect('setting.db')
    conn.cursor().execute(query)
    conn.commit()
    conn.close()


def searching(msg, message):
    content_type, chat_type, chat_id = telepot.glance(msg)
    print(content_type, chat_type, chat_id)

    i = 0
    while True:
        try:
            dot = ['', '.', '..', '...']
            conn = sqlite3.connect('setting.db')
            c = conn.cursor()
            check = c.execute("SELECT chatStatus FROM users WHERE userid = '" + str(chat_id) + "'").fetchone()[0]
            userToChat = c.execute("SELECT userToChat FROM users WHERE userid = '" + str(chat_id) + "'").fetchone()[0]
            conn.close()
            if check == 'occuped':
                stage[chat_id] = userToChat
                bot.editMessageText(telepot.message_identifier(message), "وضعیت: متصل")
                bot.sendMessage(chat_id, "اکنون می‌توانید با مخاطب صحبت کنید",
                                reply_markup=ReplyKeyboardMarkup(
                                    keyboard=[
                                        [KeyboardButton(text="پایان گفتگو")]
                                    ]
                                ))
                break
            else:
                if i == 3:
                    i = 0
                else:
                    i += 1
                bot.editMessageText(telepot.message_identifier(message), "وضعیت: در حال جستجوی مخاطب" + dot[i])
                time.sleep(0.7)
        except:
            pass


def start(msg):
    content_type ,chat_type, chat_id = telepot.glance(msg)
    print(content_type, chat_type, chat_id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Press me', callback_data='press')],
    ])
    try:
        reply = msg['reply_to_message']['message_id']
    except:
        reply = None
    try:
        stage[chat_id]
    except:
        conn = sqlite3.connect('setting.db')
        c = conn.cursor()
        try:
            stage[chat_id] = c.execute("SELECT userToChat FROM users WHERE userid = '" + str(chat_id) + "'").fetchone()[
                0]
        except:
            stage[chat_id] = 0
        finally:
            conn.close()
    try:
        conn = sqlite3.connect('setting.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE userid = '" + str(chat_id) + "'").fetchone()[0]
        conn.close()
    except:
        query("INSERT INTO users (userid) VALUES ('" + str(chat_id) + "')")

    if content_type == 'text' and msg['text'] == '/start':
        welcome = "سلام خوش آمدید شما می‌توانید به کمک من با یک غریبه هم صحبت شوید. بر روی دکمه جستجو کلیک کنید"
        bot.sendMessage(chat_id, welcome,
        reply_markup = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="جستجوی مخاطب")]
            ]
        ))
    elif content_type == 'text' and msg['text'] == "جستجوی مخاطب":
        stage[chat_id] = 'start'
        conn = sqlite3.connect('setting.db')
        c = conn.cursor()
        c.execute("UPDATE users SET chatStatus = 'active' WHERE userid = '" + str(chat_id) + "'")
        conn.commit()
        conn.close()
        try:
            conn = sqlite3.connect('setting.db')
            c = conn.cursor()
            userToChat = c.execute("SELECT userid FROM users WHERE chatStatus = 'active' AND NOT userid = '" + str(
                chat_id) + "'").fetchone()[0]
            conn.close()
            query("UPDATE users SET chatStatus = 'occuped', userToChat = '" + str(
                userToChat) + "'  WHERE userid = '" + str(chat_id) + "'")
            query(
                "UPDATE users SET chatStatus = 'occuped', userToChat = '" + str(chat_id) + "'  WHERE userid = '" + str(
                    userToChat) + "'")
            stage[chat_id] = userToChat
            bot.sendMessage(chat_id, 'وضعیت: متصل')
            bot.sendMessage(chat_id, "اکنون می‌توانید با مخاطب صحبت کنید",
                            reply_markup=ReplyKeyboardMarkup(
                                keyboard=[
                                    [KeyboardButton(text="پایان گفتگو")]
                                ]
                            ))
        except:
            message = bot.sendMessage(chat_id, 'وضعیت: در حال جستجو')
            t = threading.Thread(target=searching, args=(msg, message,))
            t.start()
    elif content_type == 'text' and msg['text'] == '/nopics':
        query("UPDATE users SET photo = 'FALSE' WHERE userid = '" + str(chat_id) + "'")
    elif content_type == 'text' and stage[chat_id] != 0:
        if content_type == 'text' and msg['text'] == "پایان گفتگو":
            # end conversation
            query("UPDATE users SET chatStatus = 'not active', userToChat = 'NULL'  WHERE userid = '" + str(
                chat_id) + "'")
            query("UPDATE users SET chatStatus = 'not active', userToChat = 'NULL'  WHERE userid = '" + str(
                stage[chat_id]) + "'")
            bot.sendMessage(stage[chat_id],
                            "پایان مکالمه، با کلیک بر روی دکمه جستجوی مخاطب، مخاطب جدید پیدا کنید",
                            reply_markup=ReplyKeyboardMarkup(
                                keyboard=[
                                    [KeyboardButton(text="جستجوی مخاطب")]
                                ]
                            ))
            bot.sendMessage(chat_id, "پایان مکالمه، با کلیک بر روی دکمه جستجوی مخاطب، مخاطب جدید پیدا کنید",
                            reply_markup=ReplyKeyboardMarkup(
                                keyboard=[
                                    [KeyboardButton(text="جستجوی مخاطب")]
                                ]
                            ))
        else:
            bot.sendMessage(stage[chat_id], msg['text'], reply_to_message_id=reply)
    elif content_type == 'photo' and stage[chat_id] != 0:
        # no pics
        conn = sqlite3.connect('setting.db')
        c = conn.cursor()
        photo = c.execute("SELECT photo FROM users WHERE userid = '" + str(stage[chat_id]) + "'").fetchone()[0]
        conn.close()
        if photo == 'TRUE':
            bot.sendPhoto(stage[chat_id], msg['photo'][0]['file_id'], reply_to_message_id=reply)
        else:
            bot.sendMessage(chat_id, 'User block the pics')
    elif content_type == 'voice' and stage[chat_id] != 0:
        bot.sendVoice(stage[chat_id], msg['voice']['file_id'], reply_to_message_id=reply)
    elif content_type == 'sticker' and stage[chat_id] != 0:
        bot.sendSticker(stage[chat_id], msg['sticker']['file_id'], reply_to_message_id=reply)
    elif content_type == 'location' and stage[chat_id] != 0:
        bot.sendLocation(stage[chat_id], msg['location']['latitude'], msg['location']['longitude'],
                         reply_to_message_id=reply)
    elif content_type == 'document' and stage[chat_id] != 0:
        bot.sendDocument(stage[chat_id], msg['document']['file_id'], reply_to_message_id=reply)
    elif content_type == 'contact' and stage[chat_id] != 0:
        bot.sendContact(stage[chat_id], msg['contact']['phone_number'], msg['contact']['first_name'],
                        reply_to_message_id=reply)
    elif content_type == 'audio' and stage[chat_id] != 0:
        bot.sendAudio(stage[chat_id], msg['audio']['file_id'], reply_to_message_id=reply)
    elif content_type == 'video' and stage[chat_id] != 0:
        bot.sendVideo(stage[chat_id], msg['video']['file_id'], reply_to_message_id=reply)
    elif content_type == 'video_note' and stage[chat_id] != 0:
        bot.sendVideoNote(stage[chat_id], msg['video_note']['file_id'], reply_to_message_id=reply)


bot.message_loop(start)
print("Bot started")
try:
    while True:
        time.sleep(8)
except KeyboardInterrupt:
    print("\nBot Stopped")
    sys.exit(0)
