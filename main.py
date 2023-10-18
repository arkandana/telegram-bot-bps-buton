# This is a sample Python script.
from typing import Final
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import requests
import pandas as pd
from datetime import datetime
import re

TOKEN: Final = '6388797473:AAEM5E65zRfy1Yueu6zGVNpq-6Xy48Mv5so'
BOT_USERNAME: Final = '@bps7401_bot'

user_state = {}
user_info = {}
temp_user_info = {}
data = {
            "name": [],
            "instansi": [],
            # "jabatan": [],
            "no_telpon": [],
            "tanggal": []
            }

class UserInfo:
    def __init__(self):
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

        self.name = ''
        # self.jabatan = ''
        self.instansi = ''
        self.no_telpon = ''
        self.tanggal = dt_string

def buku_tamu():
    for key in user_info:
        data['name'].append(user_info[key].name)
        data['instansi'].append(user_info[key].instansi)
        # data['jabatan'].append(user_info[key].jabatan)
        data['no_telpon'].append(user_info[key].no_telpon)
        data['tanggal'].append(user_info[key].tanggal)

    now = datetime.now()
    dt_string = now.strftime("%d%m%Y")
    df = pd.DataFrame(data)
    df.to_excel(dt_string + '.xlsx')


async def command_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_state[chat_id] = 0

    await send_welcome_get_name(context.bot, chat_id)

async def send_welcome_get_name(bot, chat_id):
    # state: 0
    message = """
    Selamat datang di bot PST BPS Kabupaten Buton. Dengan siapa saya berbicara?
    """

    user_state[chat_id] = 1
    await bot.send_message(chat_id, message)

async def command_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if chat_id not in user_state:
        user_state[chat_id] = 0

    if user_state[chat_id] != 5:
        await send_restriction(context.bot, chat_id)
    else:
        message = f'Nama Anda adalah {temp_user_info[chat_id].name}'

        await context.bot.send_message(chat_id, message)

async def send_welcome_get_instansi(bot, chat_id):
    # state: 1
    message = f"""
    Baiklah, {temp_user_info[chat_id].name}. Untuk keperluan pendataan, silahkan masukkan asal Instansi saudara. 
    """

    user_state[chat_id] = 2
    await bot.send_message(chat_id, message)

# async def send_welcome_get_jabatan(bot, chat_id):
#     # state: 2
#     message = f"""
#     Kemudian. silahkan masukkan jabatan anda
#     """
#
#     user_state[chat_id] = 3
#     await bot.send_message(chat_id, message)

async def send_welcome_get_no_telpon(bot, chat_id):
    # state: 3
    message = f"""
    Silahkan masukkan No. Telepon anda 
    """

    user_state[chat_id] = 3
    #user_state[chat_id] = 4
    await bot.send_message(chat_id, message)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    message = update.message.text

    if len(message) == 0:
        return

    if chat_id not in user_state:
        user_state[chat_id] = 0

    state = user_state[chat_id]

    if state == 0:
        await command_start(update, context)
    elif state == 1:
        temp_user_info[chat_id] = UserInfo()
        temp_user_info[chat_id].name = message.title()
        await send_welcome_get_instansi(context.bot, chat_id)
    elif state == 2:
        temp_user_info[chat_id].instansi = message.title()
        #await send_welcome_get_jabatan(context.bot, chat_id)
        await send_welcome_get_no_telpon(context.bot, chat_id)
    # elif state == 3:
    #     temp_user_info[chat_id].jabatan = message.title()
    #     await send_welcome_get_no_telpon(context.bot, chat_id)
    elif state == 3:
    # elif state == 4:
        myre = '^(08|[+]*628)[0-9]{9,14}'
        if re.match(myre, message):
            temp_user_info[chat_id].no_telpon = message
            await send_welcome_confirmation(context.bot, chat_id)
        else:
            message = f"""
            Nomor Telepon anda Tidak Valid 
            """
            await context.bot.send_message(chat_id, message)
            await send_welcome_get_no_telpon(context.bot, chat_id)


async def send_welcome_confirmation(bot, chat_id):
    # state: 2
    message = f"""
    Nama: {temp_user_info[chat_id].name}
    Instansi: {temp_user_info[chat_id].instansi}
    No. Telepon: {temp_user_info[chat_id].no_telpon}
    Apakah data tersebut sudah benar?
    """.replace('\n    ', '\n')
    buttons = [
        [
            InlineKeyboardButton('Ya', callback_data=str(chat_id)+',confirm_y'),
            InlineKeyboardButton('Tidak', callback_data=str(chat_id)+',confirm_n')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    user_state[chat_id] = 3
    await bot.send_message(chat_id, message, reply_markup=reply_markup)

async def callback_welcome_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    await query.answer()

    query_data = query.data.split(',')
    chat_id = int(query_data[0])
    callback_data = query_data[1]

    if callback_data == 'confirm_y':
        await query.edit_message_text(f'{query.message.text}\nJawaban: Ya')
        await context.bot.send_message(chat_id, 'Terimakasih telah menggunakan layanan kami :)')
        user_info[chat_id] = temp_user_info[chat_id]
        del temp_user_info[chat_id]
        user_state[chat_id] = 4
        # user_state[chat_id] = 5
        buku_tamu()
        await send_menu(context.bot, chat_id)
    elif callback_data == 'confirm_n':
        await query.edit_message_text(f'{query.message.text}\nJawaban: Tidak')
        await context.bot.send_message(chat_id, 'Baik, silahkan ulangi masukan data.')

        user_state[chat_id] = 0
        await send_welcome_get_name(context.bot, chat_id)

async def send_restriction(bot, chat_id):
    # state not 6
    message = """
    Maaf, Anda harus memulai bot dengan mengetik '/start' terlebih dahulu.
    """

    await bot.send_message(chat_id, message)

async def send_menu(bot, chat_id):
    # state: 5
    message = f"""
    Halo, {user_info[chat_id].name}!
    Selamat Datang di layanan PST BPS Kabupaten Buton.
    Silahkan Pilih Menu layanan:
        1. Publikasi 
        2. Tabel Statis
        3. Berita Resmi Statistik 
        4. Infografis 
        5. Hubungi Operator 
    Silahkan masukkan perintah menu dengan cara balas (/nomor keyword)
    Contoh: /2 pdrb'
    
    Jika ingin berhenti menggunakan bot, silahkan klik /stop
    """.replace('\n    ', '\n')

    user_state[chat_id] = 5
    #user_state[chat_id] = 6
    await bot.send_message(chat_id, message)

async def command_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    # chat_id = str(chat_id)
    bot = context.bot

    if chat_id not in user_state:
        user_state[chat_id] = 0

    if user_state[chat_id] < 5:
        await send_restriction(bot, chat_id)
    else:
        await send_menu(bot, chat_id)

async def command_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = f"""
    Terima Kasih Telah Menggunakan layanan Bot kami! 😊.
    Silahkan isi survei kepuasan layanan bot PST BPS Kabupaten Buton pada link di bawah ini:
    s.bps.go.id/SurveiKepuasanBotPSTBPSBUTON
    
    Jika ingin menggunakan bot kembali klik /start
    """.replace('\n    ', '\n')
    user_state[update.message.chat_id] = 0
    await context.bot.send_message(update.message.chat_id, message)


async def handle_response_publikasi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text: str = update.message.text
    kata = ' '.join(text.split()[1:])

    if update.message.chat_id not in user_state:
        user_state[update.message.chat_id] = 0

    if user_state[update.message.chat_id] < 5:
        await send_restriction(context.bot,  update.message.chat_id)
    else:
        api_key = '229df79fff1047d36f7f6ae83beac10b'
        url = 'https://webapi.bps.go.id/v1/api/list/'
        # keyword: str = ''
        # if len(kata) >= 0:
        #     keyword = ' '.join(kata)

        params = {'domain': 7401, 'model': 'publication', 'keyword': kata, 'lang': 'ind', 'key': api_key}
        r = requests.get(url=url, params=params)
        data = r.json()
        try:
            hal = data['data'][0]
            hal = hal['pages']

            df2 = pd.DataFrame()
            for i in range(1, hal + 1):
                params = {'domain': 7401, 'model': 'publication', 'page': i, 'keyword': kata, 'lang': 'ind', 'key': api_key}
                r = requests.get(url=url, params=params)
                data = r.json()
                data2 = data['data'][1]

                df = pd.DataFrame.from_dict(data2)
                df2 = pd.concat([df, df2], ignore_index=True)

            # for i in range (len(df2.pdf)):
            #   await context.bot.send_document(update.message.chat_id, df2.pdf[i])
            keyboard = []
            pdf_len = len(df2.pdf)

            for i in range(pdf_len):
                keyboard.append(
                    [InlineKeyboardButton(df2.title[i], callback_data=str(update.message.chat_id), url=df2.pdf[i])])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text('Please choose:', reply_markup=reply_markup)
            await update.message.reply_text('Jika ingin kembali ke menu awal silahkan klik /menu')
            print("BERHASILK HORE")
        except IndexError:
            await update.message.reply_text('Tidak ada Publikasi dengan keyword ' + str(kata))
            await update.message.reply_text('Jika ingin kembali ke menu awal silahkan klik /menu')


async def handle_response_tabel_statis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text: str = update.message.text
    kata = ' '.join(text.split()[1:])

    if update.message.chat_id not in user_state:
        user_state[update.message.chat_id] = 0

    if user_state[update.message.chat_id] < 5:
        await send_restriction(context.bot,  update.message.chat_id)
    else:
        api_key = '229df79fff1047d36f7f6ae83beac10b'
        url = 'https://webapi.bps.go.id/v1/api/list/'

        # keyword: str = ''
        # if len(kata) >= 0:
        #     keyword = ' '.join(kata)

        params = {'domain': 7401, 'model': 'statictable', 'keyword': kata, 'lang': 'ind', 'key': api_key}
        r = requests.get(url=url, params=params)
        data = r.json()
        try:
            hal = data['data'][0]
            hal = hal['pages']

            df2 = pd.DataFrame()
            for i in range(1, hal + 1):
                params = {'domain': 7401, 'model': 'statictable', 'page': i, 'keyword': kata, 'lang': 'ind', 'key': api_key}
                r = requests.get(url=url, params=params)
                data = r.json()
                data2 = data['data'][1]

                df = pd.DataFrame.from_dict(data2)
                df2 = pd.concat([df, df2], ignore_index=True)

            keyboard = []
            excel_len = len(df2.excel)

            for i in range(excel_len):
                keyboard.append(
                    [InlineKeyboardButton(df2.title[i], callback_data=str(update.message.chat_id), url=df2.excel[i])])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text('Silahkan PIlih:', reply_markup=reply_markup)
            await update.message.reply_text('Jika ingin kembali ke menu awal silahkan klik /menu')
            print("BERHASILK HORE")
        except IndexError:
            await update.message.reply_text('Tidak ada Tabel Statis dengan keyword ' + str(kata))
            await update.message.reply_text('Jika ingin kembali ke menu awal silahkan klik /menu')


async def handle_response_infografis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text: str = update.message.text
    kata = ' '.join(text.split()[1:])

    if update.message.chat_id not in user_state:
        user_state[update.message.chat_id] = 0

    if user_state[update.message.chat_id] < 5:
        await send_restriction(context.bot,  update.message.chat_id)
    else:
        api_key = '229df79fff1047d36f7f6ae83beac10b'
        url = 'https://webapi.bps.go.id/v1/api/list/'
        # params = {'domain': 7401, 'model': 'publication', 'keyword': '', 'lang': 'ind', 'key': api_key}
        keyword: str = ''
        if len(kata) >= 0:
            keyword = ' '.join(kata)

        params = {'domain': 7401, 'model': 'infographic', 'keyword': kata, 'lang': 'ind', 'key': api_key}
        r = requests.get(url=url, params=params)
        data = r.json()
        try:
            hal = data['data'][0]
            hal = hal['pages']

            df2 = pd.DataFrame()
            for i in range(1, hal + 1):
                params = {'domain': 7401, 'model': 'infographic', 'page': i, 'keyword': kata, 'lang': 'ind', 'key': api_key}
                r = requests.get(url=url, params=params)
                data = r.json()
                data2 = data['data'][1]

                df = pd.DataFrame.from_dict(data2)
                df2 = pd.concat([df, df2], ignore_index=True)

            for i in range(len(df2.img)):
                await context.bot.send_photo(update.message.chat_id, df2.img[i])

            await update.message.reply_text('Jika ingin kembali ke menu awal silahkan klik /menu')
            print("BERHASILK HORE")
        except IndexError:
            await update.message.reply_text('Tidak ada Infografis dengan keyword ' + str(kata))
            await update.message.reply_text('Jika ingin kembali ke menu awal silahkan klik /menu')


async def handle_response_brs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text: str = update.message.text
    kata = ' '.join(text.split()[1:])

    if update.message.chat_id not in user_state:
        user_state[update.message.chat_id] = 0

    if user_state[update.message.chat_id] < 5:
        await send_restriction(context.bot,  update.message.chat_id)
    else:
        api_key = '229df79fff1047d36f7f6ae83beac10b'
        url = 'https://webapi.bps.go.id/v1/api/list/'
        keyword: str = ''
        if len(kata) >= 0:
            keyword = ' '.join(kata)

        params = {'domain': 7401, 'model': 'pressrelease', 'keyword': kata, 'lang': 'ind', 'key': api_key}
        r = requests.get(url=url, params=params)
        data = r.json()
        try:
            hal = data['data'][0]
            hal = hal['pages']

            df2 = pd.DataFrame()
            for i in range(1, hal + 1):
                params = {'domain': 7401, 'model': 'pressrelease', 'page': i, 'keyword': kata, 'lang': 'ind',
                          'key': api_key}
                r = requests.get(url=url, params=params)
                data = r.json()
                data2 = data['data'][1]

                df = pd.DataFrame.from_dict(data2)
                df2 = pd.concat([df, df2], ignore_index=True)

            # for i in range (len(df2.pdf)):
            #   await context.bot.send_document(update.message.chat_id, df2.pdf[i])
            keyboard = []
            pdf_len = len(df2.pdf)

            for i in range(pdf_len):
                keyboard.append(
                    [InlineKeyboardButton(df2.title[i], callback_data=str(update.message.chat_id), url=df2.pdf[i])])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text('Silahkan Pilih:', reply_markup=reply_markup)

            await update.message.reply_text('Jika ingin kembali ke menu awal silahkan klik /menu')
            print("BERHASILK HORE")
        except IndexError:
            await update.message.reply_text('Tidak ada Berita Resmi Statistik dengan keyword ' + str(kata))
            await update.message.reply_text('Jika ingin kembali ke menu awal silahkan klik /menu')


async def handle_response_operator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id not in user_state:
        user_state[update.message.chat_id] = 0

    if user_state[update.message.chat_id] < 5:
        await send_restriction(context.bot,  update.message.chat_id)
    else:
        listt = ['WhatsApp', 'Facebook', 'Instagram']
        url = ['wa.me/6289670045026', 'https://www.facebook.com/profile.php?id=100076987442090', 'https://www.instagram.com/bpskabbuton/']
        keyboard = []
        for i in range(len(listt)):
            keyboard.append(
                [InlineKeyboardButton(listt[i], callback_data=str(update.message.chat_id), url=url[i])])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Silahkan Pilih', reply_markup=reply_markup)

        await update.message.reply_text('Jika ingin kembali ke menu awal silahkan klik /menu')
        print("BERHASILK HORE")


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    query_data = query.data.split(',')
    chat_id = query_data[0]
    btn = query_data[1]
    await query.answer()
    await context.bot.send_message(chat_id, btn)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler('start', command_start))
    app.add_handler(CommandHandler('menu', command_menu))
    app.add_handler(CommandHandler('stop', command_stop))
    app.add_handler(CommandHandler('1', handle_response_publikasi))
    app.add_handler(CommandHandler('2', handle_response_tabel_statis))
    app.add_handler(CommandHandler('3', handle_response_brs))
    app.add_handler(CommandHandler('4', handle_response_infografis))
    app.add_handler(CommandHandler('5', handle_response_operator))
    app.add_handler(CommandHandler('help', handle_response_operator))
    app.add_handler(CallbackQueryHandler(callback_welcome_confirmation))

    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.add_handler(CallbackQueryHandler(button))
    # app.add_error_handler(error)

    print('Polling....')
    app.run_polling(poll_interval=3)
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
