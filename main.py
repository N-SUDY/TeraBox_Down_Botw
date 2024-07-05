import os
import re
import requests
import telebot
from time import time
from flask import Flask, jsonify
from threading import Thread


bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))
print('Bot Connected')
app = Flask(__name__)

# Ensure the Videos directory exists
if not os.path.exists('Videos'):
    os.makedirs('Videos')

# Function to format the progress bar
def format_progress_bar(filename, percentage, done, total_size, status, speed, user_mention, user_id):
    bar_length = 10
    filled_length = int(bar_length * percentage / 100)
    bar = '★' * filled_length + '☆' * (bar_length - filled_length)

    def format_size(size):
        size = int(size)
        if size < 1024:
            return f"{size} B"
        elif size < 1024 ** 2:
            return f"{size / 1024:.2f} KB"
        elif size < 1024 ** 3:
            return f"{size / 1024 ** 2:.2f} MB"
        else:
            return f"{size / 1024 ** 3:.2f} GB"

    return (
        f"┏ ғɪʟᴇɴᴀᴍᴇ: <b>{filename}</b>\n"
        f"┠ [{bar}] {percentage:.2f}%\n"
        f"┠ ᴘʀᴏᴄᴇssᴇᴅ: {format_size(done)} ᴏғ {format_size(total_size)}\n"
        f"┠ sᴛᴀᴛᴜs: <b>{status}</b>\n"
        f"┠ sᴘᴇᴇᴅ: <b>{format_size(speed)}/s</b>\n"
        f"┖ ᴜsᴇʀ: {user_mention} | ɪᴅ: <code>{user_id}</code>"
    )

# Function to download video
def download_video(url, chat_id, message_id, user_mention, user_id):
    response = requests.get(f'https://teraboxvideodownloader.nepcoderdevs.workers.dev/?url={url}')
    data = response.json()

    if not data['response'] or len(data['response']) == 0:
        raise Exception('No response data found')

    resolutions = data['response'][0]['resolutions']
    fast_download_link = resolutions['Fast Download']
    video_title = re.sub(r'[<>:"/\\|?*]+', '', data['response'][0]['title'])
    video_path = os.path.join('Videos', f"{video_title}.mp4")

    with open(video_path, 'wb') as video_file:
        video_response = requests.get(fast_download_link, stream=True)

        total_length = video_response.headers.get('content-length')
        if total_length is None:  # no content length header
            video_file.write(video_response.content)
        else:
            downloaded_length = 0
            total_length = int(total_length)
            start_time = time()
            last_percentage_update = 0
            for chunk in video_response.iter_content(chunk_size=4096):
                downloaded_length += len(chunk)
                video_file.write(chunk)
                elapsed_time = time() - start_time
                percentage = 100 * downloaded_length / total_length
                speed = downloaded_length / elapsed_time

                if percentage - last_percentage_update >= 7:  # update every 7%
                    progress = format_progress_bar(
                        video_title,
                        percentage,
                        downloaded_length,
                        total_length,
                        'Downloading',
                        speed,
                        user_mention,
                        user_id
                    )
                    bot.edit_message_text(progress, chat_id, message_id, parse_mode='HTML')
                    last_percentage_update = percentage

    return video_path, video_title, total_length

# Start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user = message.from_user
    inline_keyboard = telebot.types.InlineKeyboardMarkup()
    inline_keyboard.add(telebot.types.InlineKeyboardButton("ᴅᴇᴠᴇʟᴏᴘᴇʀ ⚡️", url="tg://user?id=1008848605"))  # Add your URL here

    bot.send_message(
        message.chat.id, 
        (
            f"ᴡᴇʟᴄᴏᴍᴇ, <a href='tg://user?id={user.id}'>{user.first_name}</a>.\n\n"
            "🌟 ɪ ᴀᴍ ᴀ ᴛᴇʀᴀʙᴏx ᴅᴏᴡɴʟᴏᴀᴅᴇʀ ʙᴏᴛ.\n"
            "sᴇɴᴅ ᴍᴇ ᴀɴʏ ᴛᴇʀᴀʙᴏx ʟɪɴᴋ ɪ ᴡɪʟʟ ᴅᴏᴡɴʟᴏᴀᴅ ᴡɪᴛʜɪɴ ғᴇᴡ sᴇᴄᴏɴᴅs\n"
            "ᴀɴᴅ sᴇɴᴅ ɪᴛ ᴛᴏ ʏᴏᴜ ✨"
        ), 
        parse_mode='HTML', 
        reply_markup=inline_keyboard
    )
# Handle messages
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    video_url = message.text
    chat_id = message.chat.id
    user = message.from_user
    user_mention = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
    user_id = user.id

    if re.match(r'http[s]?://.*tera', video_url):
        download_msg = bot.send_message(chat_id, 'ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ʏᴏᴜʀ ᴠɪᴅᴇᴏ...')
        try:
            video_path, video_title, video_size = download_video(video_url, chat_id, download_msg.message_id, user_mention, user_id)
            bot.edit_message_text('sᴇɴᴅɪɴɢ ʏᴏᴜ ᴛʜᴇ ᴍᴇᴅɪᴀ...🤤', chat_id, download_msg.message_id)
    

            video_size_mb = video_size / (1024 * 1024)
            
            bot.send_video(os.getenv('DUMP_CHANNEL_ID'), open(video_path, 'rb'), caption=f"✨ {video_title}\n📀 {video_size_mb:.2f} MB\n👤 ʟᴇᴇᴄʜᴇᴅ ʙʏ : {user_mention}\n📥 ᴜsᴇʀ ʟɪɴᴋ: tg://user?id={user_id}", parse_mode='HTML')
            bot.send_video(chat_id, open(video_path, 'rb'), caption=f"✨ {video_title}\n👤 ʟᴇᴇᴄʜᴇᴅ ʙʏ : {user_mention}\n📥 ᴜsᴇʀ ʟɪɴᴋ: tg://user?id={user_id}", parse_mode='HTML')
                      
            bot.send_sticker(chat_id, "CAACAgIAAxkBAAEZdwRmJhCNfFRnXwR_lVKU1L9F3qzbtAAC4gUAAj-VzApzZV-v3phk4DQE")
            bot.delete_message(chat_id, download_msg.message_id)
            bot.delete_message(chat_id, message.message_id)


            os.remove(video_path)
        except Exception as e:
            bot.edit_message_text(f'Download failed: {str(e)}', chat_id, download_msg.message_id)
    else:
        bot.send_message(chat_id, 'ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ᴛᴇʀᴀʙᴏx ʟɪɴᴋ.')

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify(status='OK'), 200

if __name__ == "__main__":
    # Start Flask app in a separate thread
    def run_flask():
        app.run(host='0.0.0.0', port=5000)

    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    # Start polling for Telegram updates
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Error in bot polling: {str(e)}")
