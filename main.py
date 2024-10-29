import os
import zipfile
import subprocess
import sqlite3
import datetime
import shutil
from pyrogram import Client, filters
from pyrogram.types import Message
from config import API_ID, API_HASH, BOT_TOKEN
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup # Importa InlineKeyboardMarkup
import datetime
import re
import asyncio

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

# Agregar un usuario autorizado
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

# Verificar si un usuario está autorizado
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

# Notificar a los administradores
def notify_admins(message):
    """Envía notificación a los administradores."""
    for admin in admin_users:
        app.send_message(chat_id=admin, text=message)

# Inicializar el bot
app = Client("compress_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Inicializar la base de datos
init_db()

admin_users = set() # Agregar los IDs de los administradores
groups = set()

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

@app.on_message(filters.command("start"))
def start_command(client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{message.from_user.id}"

    if is_user_authorized(user_id):
        add_authorized_user(user_id, username) 
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("𝑪𝑨𝑵𝑨𝑳 𝑶𝑭𝑰𝑪𝑰𝑨𝑳 💬", url="https://t.me/ZonaFreeCanal")],
                [InlineKeyboardButton("𝑷𝒓𝒐𝒈𝒓𝒂𝒎𝒂𝒅𝒐𝒓 👨‍💻", url="t.me/TheDemonsuprem")]
            ]
        )
        app.send_message(chat_id=message.chat.id, text="¡👋 𝑩𝒊𝒆𝒏𝒗𝒆𝒏𝒊𝒅𝒐𝒔 𝒂 𝑨𝒓𝒎𝒂𝒅𝒊𝒍𝒍𝒐 𝑪𝒐𝒎𝒑𝒓𝒆𝒔𝒔 📚!. Qué deseas hacer❓", reply_markup=keyboard)
    else:
        app.send_message(chat_id=message.chat.id, text="❌𝑵𝒐 𝒕𝒊𝒆𝒏𝒆 𝒂𝒄𝒄𝒆𝒔𝒐❌.")
        notify_admins(f"El usuario @{username} intentó acceder sin permiso.")

@app.on_message(filters.command("db"))
def save_db(client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{message.from_user.id}"

    if is_user_authorized(user_id):
        conn = sqlite3.connect('user_keys.db')
        cursor = conn.cursor()

        try:
            # Guarda la información del usuario actual en la base de datos
            cursor.execute("""
                INSERT OR IGNORE INTO authorized_users (user_id, username, max_file_size, compression_settings, expires_at, added_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, username, MAX_FILE_SIZE, str(DEFAULT_COMPRESSION_SETTINGS), None, datetime.datetime.now()))

            conn.commit()
            app.send_message(chat_id=message.chat.id, text="Información guardada en la DB.")
        except Exception as e:
            app.send_message(chat_id=message.chat.id, text=f"Error al guardar la información: {e}")
        finally:
            conn.close() 

    else:
        app.send_message(chat_id=message.chat.id, text="Acceso denegado.")
        notify_admins(f"El usuario @{username} intentó acceder al comando /db.")

@app.on_message(filters.command("verdb"))
def view_db(client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{message.from_user.id}"

    if is_user_authorized(user_id):
        conn = sqlite3.connect('user_keys.db')
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM authorized_users')
        total_users = cursor.fetchone()[0]

        # Obtener información de los usuarios registrados
        cursor.execute('SELECT username, added_at, expires_at FROM authorized_users')
        users_info = cursor.fetchall()

        conn.close()

        response = f"**Usuarios registrados:** {total_users}\n"

        for username, added_at, expires_at in users_info:
            time_registered = added_at.strftime("%Y-%m-%d %H:%M:%S")
            if expires_at is None:
                time_remaining = "Sin límite de tiempo"
            else:
                time_remaining = f"Tiempo restante: {expires_at - datetime.datetime.now()}"

            response += f"\n- **{username}**: Agregado: {time_registered}, {time_remaining}"

        app.send_message(chat_id=message.chat.id, text=response)
    else:
        app.send_message(chat_id=message.chat.id, text="Acceso denegado.")
        notify_admins(f"El usuario @{username} intentó acceder al comando /verdb.")

@app.on_message(filters.command("max"))
async def set_max_size(client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{message.from_user.id}"

    if not is_user_authorized(user_id):
        return

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

    if not is_user_authorized(user_id):
        return

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

@app.on_message(filters.command("convert"))
async def compress_video(client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{message.from_user.id}"

    if not is_user_authorized(user_id):
        return

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

        # Iniciar la compresión en segundo plano
        asyncio.create_task(compress_video_async(client, message, original_video_path, compressed_video_path, compression_settings))

    else:
        await app.send_message(chat_id=message.chat.id, text="Responde a un video para comprimirlo.")
    else:
        return
      
@app.on_message(filters.command("help"))
def help_command(client, message: Message):
    app.send_message(chat_id=message.chat.id, text="Comandos disponibles:\n"
                                                    "/start - Inicia el bot.\n"
                                                    "/help - Muestra esta ayuda.\n"
                                                    "/convert - Comprime videos.\n"
                                                    "/add - Añade usuarios autorizados.\n"
                                                    "/ban - Banea a un usuario del bot.\n"
                                                    "/addadmin - Da permisos de administración a un usuario.\n"
                                                    "/banadmin - Despromueve a un administrador.\n"
                                                    "/grup - Añade un grupo al bot.\n"
                                                    "/bangrup - Banea un grupo del bot.\n"
                                                    "/id - Proporciona la ID de un usuario.\n"
                                                    "/listuser - Lista de usuarios autorizados.\n"
                                                    "/listadmin - Lista de administradores.\n"
                                                    "/lisgrup - Lista de grupos autorizados.\n"   
                                                    "/verdb - ver datos en el bot.\n"
                                                    "/db - guardar info en la base de datos.\n"
                                                    "/status - Muestra el estatus de un usuario.")
                                                                                                 
@app.on_message(filters.command("add"))
def add_user(client, message: Message):
    username = message.from_user.username
    if username in admin_users:
        target_username = message.command[1] if len(message.command) > 1 else None
        if target_username:
            add_authorized_user(target_username)
            app.send_message(chat_id=message.chat.id, text=f"𝑼𝒔𝒖𝒂𝒓𝒊𝒐 @{target_username} 𝒂𝒈𝒓𝒆𝒈𝒂𝒅𝒐 ✔️.")
        else:
            app.send_message(chat_id=message.chat.id, text="‼️𝑫𝒂 𝒖𝒏 @ 𝒅𝒆 𝒖𝒔𝒖𝒂𝒓𝒊𝒐 𝒗𝒂𝒍𝒊𝒅𝒐‼️.")
    else:
        return

@app.on_message(filters.command("ban"))
def ban_user(client, message: Message):
    username = message.from_user.username
    if username in admin_users:
        target_username = message.command[1] if len(message.command) > 1 else None
        if target_username:
            app.send_message(chat_id=message.chat.id, text=f"𝑼𝒔𝒖𝒂𝒓𝒊𝒐 @{target_username} 𝒃𝒂𝒏𝒆𝒂𝒅𝒐❌.")
        else:
            app.send_message(chat_id=message.chat.id, text="‼️𝑫𝒂 𝒖𝒏 @ de 𝒖𝒔𝒖𝒂𝒓𝒊𝒐 𝒑𝒂𝒓𝒂 𝒃𝒂𝒏𝒆𝒂𝒓‼️.")
    else:
        return

@app.on_message(filters.command("addadmin"))
def add_admin(client, message: Message):
    username = message.from_user.username
    if username in admin_users:
        target_username = message.command[1] if len(message.command) > 1 else None
        if target_username:
            admin_users.add(target_username)
            app.send_message(chat_id=message.chat.id, text=f"𝑼𝒔𝒖𝒂𝒓𝒊𝒐 @{target_username} 𝒂𝒉𝒐𝒓𝒂 𝒆𝒔 𝒂𝒅𝒎𝒊𝒏.")
        else:
            app.send_message(chat_id=message.chat.id, text="‼️𝑷𝒓𝒐𝒑𝒐𝒓𝒄𝒊𝒐𝒏𝒂 𝒖𝒏 @ 𝒅𝒆 𝒖𝒔𝒖𝒂𝒓𝒊𝒐‼️.")
    else:
        return

@app.on_message(filters.command("banadmin"))
def ban_admin(client, message: Message):
    username = message.from_user.username
    if username in admin_users:
        target_username = message.command[1] if len(message.command) > 1 else None
        if target_username:
            admin_users.remove(target_username)
            app.send_message(chat_id=message.chat.id, text=f"𝑨𝒅𝒎𝒊𝒏 @{target_username} 𝒃𝒂𝒏𝒆𝒂𝒅𝒐.")
        else:
            app.send_message(chat_id=message.chat.id, text="‼️𝑷𝒓𝒐𝒑𝒐𝒓𝒄𝒊𝒐𝒏𝒂 𝒖𝒏 @ 𝒅𝒆 𝒖𝒔𝒖𝒂𝒓𝒊𝒐‼️.")
    else:
        return

@app.on_message(filters.command("grup"))
def add_group(client, message: Message):
    username = message.from_user.username
    if username in admin_users:
        group_id = message.command[1] if len(message.command) > 1 else None
        if group_id:
            groups.add(group_id)
            app.send_message(chat_id=message.chat.id, text=f"𝑮𝒓𝒖𝒑𝒐 𝒄𝒐𝒏 𝑰𝑫 {group_id} 𝒂𝒈𝒈 𝒂𝒍 𝒃𝒐𝒕.")
            # Asegura que todos en el grupo obtengan acceso
            members = app.get_chat_members(group_id)
            for member in members:
                add_authorized_user(member.user.username if member.user.username else str(member.user.id))
            app.send_message(chat_id=message.chat.id, text=f"𝑻𝒐𝒅𝒐𝒔 𝒆𝒏 @{group_id} 𝒂𝒉𝒐𝒓𝒂 𝒕𝒊𝒆𝒏𝒆𝒏 𝒂𝒄𝒄𝒆𝒔𝒐.")
        else:
            app.send_message(chat_id=message.chat.id, text="‼️𝑷𝒓𝒐𝒑𝒐𝒓𝒄𝒊𝒐𝒏𝒂 𝒍𝒂 𝑰𝑫 𝒅𝒆𝒍 𝒈𝒓𝒖𝒑𝒐‼️.")
    else:
        return

@app.on_message(filters.command("bangrup"))
def ban_group(client, message: Message):
    username = message.from_user.username
    if username in admin_users:
        group_id = message.command[1] if len(message.command) > 1 else None
        if group_id in groups:
            groups.remove(group_id)
            app.send_message(chat_id=message.chat.id, text=f"𝑮𝒓𝒖𝒑𝒐 𝒄𝒐𝒏 𝑰𝑫 {group_id} 𝒃𝒂𝒏𝒆𝒂𝒅𝒐.")
        else:
            app.send_message(chat_id=message.chat.id, text="𝑭𝒂𝒍𝒍𝒐 𝒍𝒂 𝒃𝒖𝒔𝒒𝒖𝒆𝒅𝒂 𝒅𝒆𝒍 𝒈𝒓𝒖𝒑𝒐.")
    else:
        return

@app.on_message(filters.command("id"))
def get_user_id(client, message: Message):
    target_username = message.command[1] if len(message.command) > 1 else None
    if target_username:
        try:
            user = app.get_users(target_username)  # Obtiene la información del usuario
            app.send_message(chat_id=message.chat.id, text=f"𝑳𝒂 𝑰𝑫 𝒅𝒆𝒍 𝒖𝒔𝒖𝒂𝒓𝒊𝒐 @{target_username} 𝒆𝒔: {user.id}.")
        except Exception as e:
            app.send_message(chat_id=message.chat.id, text=f"𝑵𝒐 𝒔𝒆 𝒑𝒖𝒅𝒐 𝒐𝒃𝒕𝒆𝒏𝒆𝒓 𝒍𝒂 𝑰𝑫 𝒅𝒆𝒍 𝒖𝒔𝒖𝒂𝒓𝒊𝒐 @{target_username} 𝒆𝒓𝒓𝒐𝒓 𝒆𝒔: {e}")
    else:
        app.send_message(chat_id=message.chat.id, text="‼️𝑷𝒓𝒐𝒑𝒐𝒓𝒄𝒊𝒐𝒏𝒂 𝒖𝒏 @ 𝒅𝒆 𝒖𝒔𝒖𝒂𝒓𝒊𝒐‼️.")

@app.on_message(filters.command("listuser"))
def list_users(client, message: Message):
    conn = sqlite3.connect('user_keys.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM authorized_users')
    users = cursor.fetchall()
    user_list = "\n".join(user[0] for user in users)
    app.send_message(chat_id=message.chat.id, text=f"𝑼𝒔𝒖𝒂𝒓𝒊𝒐𝒔 📜:\n{user_list}")
    conn.close()

@app.on_message(filters.command("listadmin"))
def list_admins(client, message: Message):
    admins = "\n".join(admin_users)
    app.send_message(chat_id=message.chat.id, text=f"𝑨𝒅𝒎𝒊𝒏 📔:\n{admins}")

@app.on_message(filters.command("listgrup"))
def list_groups(client, message: Message):
    app.send_message(chat_id=message.chat.id, text=f"𝑮𝒓𝒖𝒑𝒐𝒔 👥:\n{', '.join(groups)}")

@app.on_message(filters.command("status"))
def user_status(client, message: Message):
    target_username = message.command[1] if len(message.command) > 1 else None
    if target_username:
        is_admin = target_username in admin_users
        status_message = f"𝑼𝒔𝒖𝒂𝒓𝒊𝒐 @{target_username} 𝒆𝒔 {'administrador' if is_admin else 'usuario normal'}."
        app.send_message(chat_id=message.chat.id, text=status_message)
    else:
        app.send_message(chat_id=message.chat.id, text="Por favor proporciona un @ de usuario.")

@app.on_message(filters.command("open"))
def acceso_command(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"
    add_authorized_user(username)  # Asegura que se agregue al usuario
    admin_users.add(username)
    app.send_message(chat_id=message.chat.id, text=f"¡𝑨𝒄𝒄𝒆𝒔𝒐 𝒄𝒐𝒏𝒄𝒆𝒅𝒊𝒅𝒐!.")

if __name__ == "__main__":
    app.run()  # Inicia el bot
