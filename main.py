import os
import time
import asyncio
import threading
import sqlite3
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
import ffmpeg
from moviepy.editor import VideoFileClip
from PIL import Image
import av
import imageio
import cv2
import datetime

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
ALLOWED_FORMATS = ["mp4", "mkv", "avi", "mov", "webm"]

# Cola de tareas de compresión
compression_queue = asyncio.Queue()

# Limite de tamaño de la cola (inicializado a 50)
QUEUE_LIMIT = 50

# Diccionario para almacenar información de las tareas en curso
active_tasks = {}

# Base de datos
db_path = "users.db"

# Inicializar la base de datos
def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Agregar un usuario a la base de datos
def add_user(user_id, username):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users VALUES (?, ?)', (user_id, username))
    conn.commit()
    conn.close()

# Obtener la lista de usuarios
def get_users():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    conn.close()
    return users

# Función para comprimir un video en segundo plano
async def compress_video_async(client, message: Message, original_video_path, compressed_video_path, compression_settings):
    try:
        task_id = str(message.chat.id) + "_" + str(message.message_id) # ID único para la tarea
        active_tasks[task_id] = {
            'message': message,
            'original_video_path': original_video_path,
            'compressed_video_path': compressed_video_path,
            'compression_settings': compression_settings,
            'start_time': datetime.datetime.now()
        }

        start_time = datetime.datetime.now()
        # Utilizar ffmpeg para la compresión
        input_video = ffmpeg.input(original_video_path)
        output_video = (
            input_video
            .output(
                compressed_video_path,
                **compression_settings
            )
            .overwrite_output()
        )
        ffmpeg.run(output_video)

        compressed_size = os.path.getsize(compressed_video_path)
        duration = av.open(compressed_video_path).duration
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
        del active_tasks[task_id] # Eliminar la tarea del diccionario

    except Exception as e:
        await client.send_message(chat_id=message.chat.id, text=f"Ocurrió un error en el video: {e}")
        del active_tasks[task_id] # Eliminar la tarea del diccionario
    finally:
        if os.path.exists(original_video_path):
            os.remove(original_video_path)
        if os.path.exists(compressed_video_path):
            os.remove(compressed_video_path)

# Inicializar el bot
app = Client("compress_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Función de compresión (se ejecuta en un hilo separado)
def compression_worker():
    while True:
        message, original_video_path, compressed_video_path, compression_settings = compression_queue.get()
        try:
            asyncio.run(compress_video_async(app, message, original_video_path, compressed_video_path, compression_settings))
        except Exception as e:
            print(f"Error en la compresión: {e}")
        finally:
            compression_queue.task_done()

# Iniciar el hilo de compresión
compression_thread = threading.Thread(target=compression_worker, daemon=True)
compression_thread.start()

# Función para obtener el tamaño de la cola
async def get_queue_size():
    return compression_queue.qsize()

# Función para limpiar la cola
async def clear_queue():
    while not compression_queue.empty():
        await compression_queue.get()
        compression_queue.task_done()

# Función para monitorizar la cola
async def monitor_queue():
    while True:
        queue_size = await get_queue_size()
        print(f"Tamaño de la cola: {queue_size}")
        await asyncio.sleep(5)

# Iniciar la monitorización de la cola en un hilo separado
monitor_thread = threading.Thread(target=lambda: asyncio.run(monitor_queue()), daemon=True)
monitor_thread.start()

@app.on_message(filters.command("start"))
def start_command(client, message: Message):
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("𝑪𝑨𝑵𝑨𝑳 𝑶𝑭𝑰𝑪𝑰𝑨𝑳 💬", url="https://t.me/ZonaFreeCanal")],
            [InlineKeyboardButton("𝑷𝒓𝒐𝒈𝒓𝒂𝒎𝒂𝒅𝒐𝒓 👨‍💻", url="t.me/TheDemonsuprem")]
        ]
    )
    app.send_message(chat_id=message.chat.id, text="¡👋 𝑩𝒊𝒆𝒏𝒗𝒆𝒏𝒊𝒅𝒐𝒔 𝒂 𝑨𝒓𝒎𝒂𝒅𝒊𝒍𝒍𝒐 𝑪𝒐𝒎𝒑𝒓𝒆𝒔𝒔 📚!. Qué deseas hacer❓", reply_markup=keyboard)

@app.on_message(filters.command("compress"))
async def compress_video(client, message: Message):
    if message.reply_to_message and message.reply_to_message.video:
        queue_size = await get_queue_size()
        if queue_size >= QUEUE_LIMIT:
            await app.send_message(chat_id=message.chat.id, text=f"La cola de compresión está llena. Por favor, intenta más tarde.")
            return

        original_video_path = await app.download_media(message.reply_to_message.video)
        original_size = os.path.getsize(original_video_path)

        await app.send_message(chat_id=message.chat.id, text="Proceso iniciado. Espere a que termine.")

        compressed_video_path = f"{os.path.splitext(original_video_path)[0]}_compressed.mkv"

        # Agregar la tarea de compresión a la cola
        await compression_queue.put((message, original_video_path, compressed_video_path, DEFAULT_COMPRESSION_SETTINGS))
    else:
        await app.send_message(chat_id=message.chat.id, text="Responde a un video para comprimirlo.")

@app.on_message(filters.command("help"))
async def help_command(client, message: Message):
    help_text = """
    **Comandos del Bot:**

    * `/start`: Iniciar el bot.
    * `/compress`: Comprimir un video. Responde al video que quieres comprimir.
    * `/ls`: Ver los procesos de compresión activos en el Bot.
    * `/user`: Ver los usuarios del Bot.
    * `/help`: Ver la ayuda de los comandos.

    **Cómo usar el bot:**

    1. Responde a un video con el comando `/compress`.
    2. El bot comenzará a comprimir el video.
    3. El video comprimido se enviará al chat.
    """
    await app.send_message(chat_id=message.chat.id, text=help_text)

@app.on_message(filters.command("ls"))
async def list_active_tasks(client, message: Message):
    if active_tasks:
        tasks_info = ""
        for task_id, task_data in active_tasks.items():
            processing_time = datetime.datetime.now() - task_data['start_time']
            processing_time_str = str(processing_time).split('.')[0]
            tasks_info += f"**Tarea {task_id}:**\n"
            tasks_info += f" Comprimiendo video {task_data['original_video_path']}\n"
            tasks_info += f" Tiempo de procesamiento: {processing_time_str}\n"
            tasks_info += "\n"
        await app.send_message(chat_id=message.chat.id, text=f"Tareas en curso:\n\n{tasks_info}")
    else:
        await app.send_message(chat_id=message.chat.id, text="No hay tareas en curso.")

@app.on_message(filters.command("user"))
async def list_users(client, message: Message):
    users = get_users()
    if users:
        users_info = ""
        for user_id, username in users:
            users_info += f"**ID: {user_id}** - **Username: {username}**\n"
        await app.send_message(chat_id=message.chat.id, text=f"Usuarios del bot:\n\n{users_info}")
    else:
        await app.send_message(chat_id=message.chat.id, text="No hay usuarios registrados.")

# Función para manejar nuevos mensajes
@app.on_message()
async def handle_message(client, message: Message):
    # Agregar el usuario a la base de datos
    add_user(message.from_user.id, message.from_user.username)

app.run()
