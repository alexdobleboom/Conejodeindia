import os
import zipfile
import subprocess
import sqlite3
import datetime
import shutil
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
import re
import asyncio
import threading

# Configuración del bot
API_ID = 24288670 # Reemplázalo con tu API_ID
API_HASH = "81c58005802498656d6b689dae1edacc" # Reemplázalo con tu API_HASH
BOT_TOKEN = "7507770865:AAFDQ0Lbuo5Ca-mTnqSa-dK_UJENs5B2v1Q" # Reemplázalo con tu token de bot

# Configuraciones del bot
MAX_FILE_SIZE = 1024 * 1024 * 1024 # Límite de tamaño de archivo (1GB)
DEFAULT_COMPRESSION_SETTINGS = {
    "resolution": "740x480",
    "crf": "32",
    "audio_bitrate": "60k",
    "fps": "24",
    "preset": "ultrafast",
    "codec": "libx265"
}

# Cola de tareas de compresión
compression_queue = asyncio.Queue()

# Inicializar la base de datos
def init_db():
    conn = sqlite3.connect('user_keys.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_keys (
            user_id INTEGER PRIMARY KEY,
            key TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS authorized_users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            max_file_size INTEGER,
            compression_settings TEXT,
            expires_at DATETIME,
            added_at DATETIME
        )
    ''')
    conn.commit()
    conn.close()

# Agregar un usuario autorizado (no se utiliza para el acceso, solo para registro)
def add_authorized_user(user_id, username, hours=0):
    conn = sqlite3.connect('user_keys.db')
    cursor = conn.cursor()
    expires_at = datetime.datetime.now() + datetime.timedelta(hours=hours) if hours > 0 else None
    cursor.execute(
        'INSERT OR REPLACE INTO authorized_users (user_id, username, max_file_size, compression_settings, expires_at, added_at) VALUES (?, ?, ?, ?, ?, ?)',
        (user_id, username, MAX_FILE_SIZE, str(DEFAULT_COMPRESSION_SETTINGS), expires_at, datetime.datetime.now())
    )
    conn.commit()
    conn.close()

# Verificar si un usuario está autorizado (no se utiliza para el acceso)
def is_user_authorized(user_id):
    conn = sqlite3.connect('user_keys.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM authorized_users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user is not None and (user[4] is None or user[4] > datetime.datetime.now())

# Obtener las configuraciones del usuario
def get_user_settings(user_id):
    conn = sqlite3.connect('user_keys.db')
    cursor = conn.cursor()
    cursor.execute('SELECT max_file_size, compression_settings FROM authorized_users WHERE user_id = ?', (user_id,))
    settings = cursor.fetchone()
    conn.close()
    return settings

# Actualizar las configuraciones del usuario
def update_user_settings(user_id, max_file_size=None, compression_settings=None):
    conn = sqlite3.connect('user_keys.db')
    cursor = conn.cursor()
    if max_file_size:
        cursor.execute('UPDATE authorized_users SET max_file_size = ? WHERE user_id = ?', (max_file_size, user_id))
    if compression_settings:
        cursor.execute('UPDATE authorized_users SET compression_settings = ? WHERE user_id = ?', (compression_settings, user_id))
    conn.commit()
    conn.close()

# Función para comprimir un video en segundo plano
async def compress_video_async(client, message: Message, original_video_path, compressed_video_path, compression_settings):
    try:
        start_time = datetime.datetime.now()
        ffmpeg_command = [
            'ffmpeg', '-y', '-i', original_video_path,
            '-s', compression_settings['resolution'],
            '-crf', compression_settings['crf'],
            '-b:a', compression_settings['audio_bitrate'],
            '-preset', compression_settings['preset'],
            '-c:v', compression_settings['codec'],
            compressed_video_path
        ]

        process = subprocess.Popen(ffmpeg_command, stderr=subprocess.PIPE, text=True, stdout=subprocess.PIPE)
        await client.send_message(chat_id=message.chat.id, text="En progreso...")

        while True:
            output = process.stderr.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                await client.send_message(chat_id=message.chat.id, text=output.strip())

        compressed_size = os.path.getsize(compressed_video_path)
        duration = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries",
                                             "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
                                             compressed_video_path])
        duration = float(duration.strip())
        duration_str = str(datetime.timedelta(seconds=duration))

        processing_time = datetime.datetime.now() - start_time
        processing_time_str = str(processing_time).split('.')[0] 

        description = (
            f"Proceso finalizado.\n"
            f"Peso original: {original_size // (1024 * 1024)} MB\n"
            f"Peso procesado: {compressed_size // (1024 * 1024)} MB\n"
            f"Tiempo de procesamiento: {processing_time_str}\n"
            f"Tiempo del video: {duration_str}\n"
            f"¡Que lo disfrute!"
        )

        await client.send_document(chat_id=message.chat.id, document=compressed_video_path, caption=description)

    except Exception as e:
        await client.send_message(chat_id=message.chat.id, text=f"Ocurrió un error en el video: {e}")
    finally:
        if os.path.exists(original_video_path):
            os.remove(original_video_path)
        if os.path.exists(compressed_video_path):
            os.remove(compressed_video_path)

# Inicializar el bot
app = Client("compress_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Inicializar la base de datos
init_db()

# Función de compresión (se ejecuta en un hilo separado)
def compression_worker():
    while True:
        message, original_video_path, compressed_video_path, compression_settings = compression_queue.get()
        try:
            compress_video_async(app, message, original_video_path, compressed_video_path, compression_settings)
        except Exception as e:
            print(f"Error en la compresión: {e}")
        finally:
            compression_queue.task_done()

# Iniciar el hilo de compresión
compression_thread = threading.Thread(target=compression_worker, daemon=True)
compression_thread.start()

@app.on_message(filters.command("start"))
def start_command(client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{message.from_user.id}"

    add_authorized_user(user_id, username) # Asegura que se agregue al usuario
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("𝑪𝑨𝑵𝑨𝑳 𝑶𝑭𝑰𝑪𝑰𝑨𝑳 💬", url="https://t.me/ZonaFreeCanal")],
            [InlineKeyboardButton("𝑷𝒓𝒐𝒈𝒓𝒂𝒎𝒂𝒅𝒐𝒓 👨‍💻", url="t.me/TheDemonsuprem")]
        ]
    )
    app.send_message(chat_id=message.chat.id, text="¡👋 𝑩𝒊𝒆𝒏𝒗𝒆𝒏𝒊𝒅𝒐𝒔 𝒂 𝑨𝒓𝒎𝒂𝒅𝒊𝒍𝒍𝒐 𝑪𝒐𝒎𝒑𝒓𝒆𝒔𝒔 📚!. Qué deseas hacer❓", reply_markup=keyboard)

@app.on_message(filters.command("convert"))
async def compress_video(client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{message.from_user.id}"

    if message.reply_to_message and message.reply_to_message.video:
        original_video_path = await app.download_media(message.reply_to_message.video)
        original_size = os.path.getsize(original_video_path)

        # Obtener las configuraciones del usuario
        max_file_size, compression_settings_str = get_user_settings(user_id)
        compression_settings = eval(compression_settings_str) # Convierte la cadena a un diccionario

        if original_size > max_file_size:
            await app.send_message(chat_id=message.chat.id, text=f"El video excede el tamaño máximo permitido ({max_file_size // (1024 * 1024)} MB).")
            return

        await app.send_message(chat_id=message.chat.id, text="Proceso iniciado. Espere a que termine.")

        compressed_video_path = f"{os.path.splitext(original_video_path)[0]}_compressed.mkv"

        # Agregar la tarea de compresión a la cola
        await compression_queue.put((message, original_video_path, compressed_video_path, compression_settings))
    else:
        await app.send_message(chat_id=message.chat.id, text="Responde a un video para comprimirlo.")

@app.on_message(filters.command("max"))
async def set_max_size(client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{message.from_user.id}"

    args = message.text.split()
    if len(args) == 2:
        try:
            new_max_size = int(args[1].replace("Gb", "").replace("MB", "").replace("KB", ""))
            if args[1].endswith("Gb"):
                new_max_size *= 1024 * 1024 * 1024
            elif args[1].endswith("MB"):
                new_max_size *= 1024 * 1024
            elif args[1].endswith("KB"):
                new_max_size *= 1024
            update_user_settings(user_id, max_file_size=new_max_size)
            app.send_message(chat_id=message.chat.id, text=f"Tamaño máximo de archivo establecido a {new_max_size} bytes.")
        except ValueError:
            app.send_message(chat_id=message.chat.id, text="Formato inválido. Usa /max seguido del tamaño en GB, MB o KB.")
    else:
        app.send_message(chat_id=message.chat.id, text="Usa /max seguido del tamaño máximo de archivo en GB, MB o KB.")

@app.on_message(filters.command("calidad"))
async def set_compression_quality(client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{message.from_user.id}"

    args = message.text.split()
    if len(args) >= 2:
        new_compression_settings = DEFAULT_COMPRESSION_SETTINGS.copy() # Crea una copia de la configuración predeterminada

        # Itera sobre los argumentos para actualizar la configuración
        for arg in args[1:]:
            key, value = arg.split("=")
            if key in new_compression_settings:
                new_compression_settings[key] = value
            else:
                app.send_message(chat_id=message.chat.id, text=f"Parámetro inválido: {key}")

        # Guarda la nueva configuración en la base de datos
        update_user_settings(user_id, compression_settings=str(new_compression_settings))
        app.send_message(chat_id=message.chat.id, text=f"Calidad de compresión actualizada.")
    else:
        app.send_message(chat_id=message.chat.id, text="Usa /calidad seguido de los parámetros de compresión separados por espacios. Ejemplo: /calidad resolution=240x240 crf=37 audio_bitrate=50k fps=10 preset=ultrafast codec=libx264")

@app.on_message(filters.command("help"))
async def help_command(client, message: Message):
    help_text = """
    **Comandos del Bot:**

    * `/start`: Iniciar el bot.
    * `/convert`: Comprimir un video. Responde al video que quieres comprimir.
    * `/max [tamaño]`: Establecer el tamaño máximo de archivo permitido para la compresión. 
                       Usa GB, MB o KB. Ejemplo: /max 500MB
    * `/calidad [parámetros]`: Establecer la calidad de compresión. 
                       Usa los parámetros: resolution, crf, audio_bitrate, fps, preset, codec. 
                       Separa los parámetros por espacios. Ejemplo: /calidad resolution=360x240 crf=32 audio_bitrate=60k
    * `/help`: Ver la ayuda de los comandos.

    **Cómo usar el bot:**

    1. Responde a un video con el comando `/convert`.
    2. El bot comenzará a comprimir el video.
    3. El video comprimido se enviará al chat.
    """
    await app.send_message(chat_id=message.chat.id, text=help_text)

app.run()
