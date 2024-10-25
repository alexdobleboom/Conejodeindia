import pyrogram
import os
import subprocess
import time
from pyrogram import Client, filters
from threading import Thread
from queue import Queue
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import sqlite3

# Reemplaza estas variables con tu token, api_hash y api_id
API_ID = "24288670"
API_HASH = "81c58005802498656d6b689dae1edacc"
BOT_TOKEN = "7507770865:AAFDQ0Lbuo5Ca-mTnqSa-dK_UJENs5B2v1Q"

# Crea la base de datos si no existe
db_path = "armadillo_compress.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        is_admin BOOLEAN DEFAULT FALSE
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS groups (
        id INTEGER PRIMARY KEY,
        is_banned BOOLEAN DEFAULT FALSE
    )
""")
conn.commit()

app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Cola de tareas
task_queue = Queue()

# Calidad de video predeterminada
default_quality = "resolution=740x480 crf=32 audio_bitrate=60k fps=28 preset=ultrafast codec=libx265"
current_quality = default_quality

# Diccionario para almacenar información del proceso en curso
process_info = {}

# Lista de IDs de administradores del bot (inicialmente vacía)
admins = []

# Función para verificar si el usuario es administrador
def is_admin(user_id):
    return user_id in admins

# Función para verificar si el grupo está baneado
def is_group_banned(group_id):
    cursor.execute("SELECT is_banned FROM groups WHERE id = ?", (group_id,))
    result = cursor.fetchone()
    return result[0] if result else False

# Función para agregar un usuario a la base de datos
def add_user(user_id, username, first_name, last_name):
    cursor.execute("""
        INSERT OR IGNORE INTO users (id, username, first_name, last_name)
        VALUES (?, ?, ?, ?)
    """, (user_id, username, first_name, last_name))
    conn.commit()

# Función para agregar un grupo a la base de datos
def add_group(group_id):
    cursor.execute("""
        INSERT OR IGNORE INTO groups (id)
        VALUES (?)
    """, (group_id,))
    conn.commit()

# Función para cambiar el estado de un usuario o grupo
def update_status(table, id, is_banned=None, is_admin=None):
    if is_banned is not None:
        cursor.execute(f"UPDATE {table} SET is_banned = ? WHERE id = ?", (is_banned, id))
    if is_admin is not None:
        cursor.execute(f"UPDATE users SET is_admin = ? WHERE id = ?", (is_admin, id))
    conn.commit()

@app.on_message(filters.command(["start"]))
async def start(client, message):
    await message.reply_text("Funcionando")

# Registrar administrador inicial
@app.on_message(filters.command(["admin_id"]))
async def set_admin(client, message):
    if not is_admin(message.from_user.id):
        await message.reply_text("Solo los administradores pueden usar este comando.")
        return
    try:
        admin_id = int(message.text.split(" ")[1])
        admins.append(admin_id)
        update_status("users", admin_id, is_admin=True)
        await message.reply_text(f"Administrador con ID {admin_id} registrado.")
    except Exception as e:
        await message.reply_text(f"Error al registrar administrador: {e}")

@app.on_message(filters.command(["acceso"]))
async def give_access(client, message):
    try:
        admins.append(message.from_user.id)
        update_status("users", message.from_user.id, is_admin=True)
        await message.reply_text("¡Ahora eres administrador!")
    except Exception as e:
        await message.reply_text(f"Error al otorgar acceso de administrador: {e}")

@app.on_message(filters.command(["video"]))
async def video_converter(client, message):
    if is_group_banned(message.chat.id):
        await message.reply_text("Este grupo está bloqueado del bot.")
        return
    await message.reply_text("Envíame un video para convertirlo.")

@app.on_message(filters.video)
async def handle_video(client, message):
    if is_group_banned(message.chat.id):
        await message.reply_text("Este grupo está bloqueado del bot.")
        return
    if message.video.file_size > 1073741824: # 1 GB
        await message.reply_text("El video es demasiado grande. El límite es 1 GB.")
        return
    file_id = message.video.file_id
    await message.reply_text("Descargando video...")
    downloaded_file = await app.download_media(file_id)
    original_size = os.path.getsize(downloaded_file)

    # Agrega información del proceso a process_info
    process_info[message.chat.id] = {
        "file": downloaded_file,
        "original_size": original_size,
        "start_time": None,
        "end_time": None,
        "video_duration": message.video.duration
    }

    # Inicia el proceso de conversión
    await message.reply_text(
        "Proceso iniciado, espera a que termine.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Cancelar", callback_data="cancel")]]
        )
    )
    task_queue.put((message.chat.id, downloaded_file, current_quality))

@app.on_message(filters.command(["calidad"]))
async def set_quality(client, message):
    if is_group_banned(message.chat.id):
        await message.reply_text("Este grupo está bloqueado del bot.")
        return
    global current_quality
    quality = message.text.split(" ")[1] if len(message.text.split(" ")) > 1 else default_quality
    current_quality = quality
    await message.reply_text(f"La calidad de conversión se ha establecido en: {quality}")

@app.on_message(filters.command(["id"]))
async def get_id(client, message):
    if is_group_banned(message.chat.id):
        await message.reply_text("Este grupo está bloqueado del bot.")
        return
    try:
        username = message.text.split(" ")[1]
        if username.startswith("@"):
            username = username[1:]
        user = await app.get_users(username)
        await message.reply_text(f"El ID de {user.first_name} {user.last_name} es: {user.id}")
    except Exception as e:
        await message.reply_text(f"Error al obtener el ID: {e}")

@app.on_message(filters.command(["borrarchiv"]))
async def borrar_archivos(client, message):
    if is_group_banned(message.chat.id):
        await message.reply_text("Este grupo está bloqueado del bot.")
        return
    try:
        # Borra todos los archivos y videos almacenados en el bot
        for filename in os.listdir():
            if filename.endswith((".mp4", ".mkv", ".avi", ".mov", ".webm", ".zip", ".rar", ".7z", ".gz", ".tar", ".bz2")):
                os.remove(filename)
        await message.reply_text("¡Todos los archivos han sido borrados!")
    except Exception as e:
        await message.reply_text(f"Error al borrar los archivos: {e}")

# Comandos de administrador
@app.on_message(filters.command(["addadmin"]) & filters.user(admins))
async def add_admin_cmd(client, message):
    try:
        username = message.text.split(" ")[1]
        if username.startswith("@"):
            username = username[1:]
        user = await app.get_users(username)
        update_status("users", user.id, is_admin=True)
        admins.append(user.id)
        await message.reply_text(f"Usuario {user.username} promovido a administrador.")
    except Exception as e:
        await message.reply_text(f"Error al promover usuario a administrador: {e}")

@app.on_message(filters.command(["adduser"]) & filters.user(admins))
async def add_user_cmd(client, message):
    try:
        username = message.text.split(" ")[1]
        if username.startswith("@"):
            username = username[1:]
        user = await app.get_users(username)
        add_user(user.id, user.username, user.first_name, user.last_name)
        await message.reply_text(f"Usuario {user.username} agregado al bot.")
    except Exception as e:
        await message.reply_text(f"Error al agregar usuario: {e}")

@app.on_message(filters.command(["banuser"]) & filters.user(admins))
async def ban_user_cmd(client, message):
    try:
        username = message.text.split(" ")[1]
        if username.startswith("@"):
            username = username[1:]
        user = await app.get_users(username)
        update_status("users", user.id, is_banned=True)
        await message.reply_text(f"Usuario {user.username} bloqueado del bot.")
    except Exception as e:
        await message.reply_text(f"Error al bloquear usuario: {e}")

@app.on_message(filters.command(["banadmin"]) & filters.user(admins))
async def ban_admin_cmd(client, message):
    try:
        username = message.text.split(" ")[1]
        if username.startswith("@"):
            username = username[1:]
        user = await app.get_users(username)
        update_status("users", user.id, is_admin=False)
        admins.remove(user.id)
        await message.reply_text(f"Usuario {user.username} ha perdido los permisos de administrador.")
    except Exception as e:
        await message.reply_text(f"Error al revocar permisos de administrador: {e}")

@app.on_message(filters.command(["grup"]) & filters.user(admins))
async def add_group_cmd(client, message):
    try:
        group_id = int(message.text.split(" ")[1])
        add_group(group_id)
        await message.reply_text(f"Grupo con ID {group_id} agregado al bot.")
    except Exception as e:
        await message.reply_text(f"Error al agregar grupo: {e}")

@app.on_message(filters.command(["bangrup"]) & filters.user(admins))
async def ban_group_cmd(client, message):
    try:
        group_id = int(message.text.split(" ")[1])
        update_status("groups", group_id, is_banned=True)
        await message.reply_text(f"Grupo con ID {group_id} bloqueado del bot.")
    except Exception as e:
        await message.reply_text(f"Error al bloquear grupo: {e}")

# Función de conversión de video (se agregó la extensión mkv)
async def convert_video(chat_id, file, quality):
    try:
        process_info[chat_id]["start_time"] = time.time()
        await app.send_chat_action(chat_id, "upload_document")
        await app.send_message(chat_id, "Procesando video...")
        # Ejecuta ffmpeg para convertir el video con la calidad actual
        subprocess.run(["ffmpeg", "-i", file, "-map", "0", "-c:v", "libx265", "-c:a", "aac", "-b:a", "60k", f"-preset", "ultrafast", f"-vf", quality, "output." + os.path.splitext(file)[1]])
        process_info[chat_id]["end_time"] = time.time()
        processed_size = os.path.getsize("output." + os.path.splitext(file)[1])

        # Calcula el tiempo de procesamiento
        processing_time = process_info[chat_id]["end_time"] - process_info[chat_id]["start_time"]

        await app.send_document(chat_id, open("output." + os.path.splitext(file)[1], "rb"), 
                               caption=f"✅ 𝙋𝙧𝙤𝙘𝙚𝙨𝙤 𝙩𝙚𝙧𝙢𝙞𝙣𝙖𝙙𝙤 𝙘𝙤𝙧𝙧𝙚𝙘𝙩𝙖𝙢𝙚𝙣𝙩𝙚 ✅\n"
                                       f"🙃 𝙏𝙖𝙢𝙖ñ𝙤 𝙤𝙧𝙞𝙜𝙞𝙣𝙖𝙡: {human_readable_size(process_info[chat_id]['original_size'])}\n"
                                       f"🙂 𝙏𝙖𝙢𝙖ñ𝙤 𝙥𝙧𝙤𝙘𝙚𝙨𝙖𝙙ೊ: {human_readable_size(processed_size)}\n"
                                       f"⌚ 𝙏𝙞𝙚𝙢্প𝙤 𝙙𝙚 𝙥𝙧𝙤𝙘𝙚𝙨𝙖𝙣𝙞𝙚𝙣𝙩𝙤: {processing_time:.2f} segundos\n"
                                       f"⏲️ 𝙏𝙞𝙚𝙢্প𝙤 𝙙𝙚𝙡 𝙫𝙞𝙙𝙚𝙤: {process_info[chat_id]['video_duration']} segundos\n"
                                       f"🎉 ¡𝙂𝙧𝙖𝙘𝙞𝙖𝙨 𝙥𝙤𝙧 𝙪𝙨𝙖𝙧 𝙖 𝘼𝙧𝙢𝙖𝙙𝙞𝙡𝙡𝙤 𝘾𝙤𝙢𝙥𝙧𝙚𝙨𝙨!🎊")
        os.remove(file)
        os.remove("output." + os.path.splitext(file)[1])
    except Exception as e:
        await app.send_message(chat_id, f"Error al procesar el video: {e}")
    finally:
        task_queue.task_done()
        del process_info[chat_id] # Elimina la información del proceso

# Función de compresión de archivos
async def compress_file(chat_id, file):
    try:
        await app.send_chat_action(chat_id, "upload_document")
        await app.send_message(chat_id, "Comprimiendo archivo...")
        # Ejecuta 7z para comprimir el archivo
        subprocess.run(["7z", "a", "output.zip", file])
        await app.send_document(chat_id, open("output.zip", "rb"), caption="Archivo comprimido.")
        os.remove(file)
        os.remove("output.zip")
    except Exception as e:
        await app.send_message(chat_id, f"Error al comprimir el archivo: {e}")

# Función de descompresión de archivos
async def uncompress_file(chat_id, file):
    try:
        await app.send_chat_action(chat_id, "upload_document")
        await app.send_message(chat_id, "Descomprimiendo archivo...")
        # Ejecuta 7z para descomprimir el archivo
        subprocess.run(["7z", "x", file])
        await app.send_message(chat_id, "Archivo descomprimido.")
        os.remove(file)
    except Exception as e:
        await app.send_message(chat_id, f"Error al descomprimir el archivo: {e}")

# Función de picar archivos (se agregó la extensión mkv)
async def split_file(chat_id, file, size):
    try:
        await app.send_chat_action(chat_id, "upload_document")
        await app.send_message(chat_id, "Pícando archivo...")
        # Ejecuta ffmpeg para picar el video en partes
        subprocess.run(["ffmpeg", "-i", file, "-c", "copy", "-segment_time", f"{size}", "-f", "segment", "-reset_timestamps", "1", "output_%03d" + os.path.splitext(file)[1]])
        await app.send_message(chat_id, "Archivo pícado en partes.")
        os.remove(file)
    except Exception as e:
        await app.send_message(chat_id, f"Error al picar el archivo: {e}")

# Función de worker para procesar las tareas en la cola
async def worker():
    while True:
        chat_id, file, quality = task_queue.get()
        try:
            if file.endswith((".mp4", ".mkv", ".avi", ".mov", ".webm")):
                await convert_video(chat_id, file, quality)
            elif file.endswith((".zip", ".rar", ".7z", ".gz", ".tar", ".bz2")):
                await uncompress_file(chat_id, file)
            elif file.endswith(".apk"):
                await compress_file(chat_id, file)
        except Exception as e:
            await app.send_message(chat_id, f"Error al procesar el archivo: {e}")
        finally:
            task_queue.task_done()

# Crea hilos trabajadores
for _ in range(5): # Crea 5 hilos trabajadores
    Thread(target=worker, daemon=True).start()

@app.on_callback_query(filters.regex("cancel"))
async def cancel_process(client, query):
    chat_id = query.message.chat.id
    if chat_id in process_info:
        file = process_info[chat_id]["file"]
        await query.message.edit_text("Cancelando proceso...")
        # Cancela el proceso de ffmpeg (puedes agregar una condición para finalizar el proceso)
        # subprocess.run(["pkill", "ffmpeg"]) # o un método más específico para matar el proceso
        await query.message.edit_text("Proceso cancelado.")
        os.remove(file)
        del process_info[chat_id]
    else:
        await query.message.edit_text("No hay proceso en curso.")

def human_readable_size(size):
    """Convierte el tamaño de un archivo a una representación legible por humanos."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"

@app.on_message(filters.document)
async def handle_document(client, message):
    if is_group_banned(message.chat.id):
        await message.reply_text("Este grupo está bloqueado del bot.")
        return
    if message.document.file_size > 1073741824: # 1 GB
        await message.reply_text("El archivo es demasiado grande. El límite es 1 GB.")
        return
    file_id = message.document.file_id
    await message.reply_text("Descargando archivo...")
    downloaded_file = await app.download_media(file_id)
    original_size = os.path.getsize(downloaded_file)

    # Agrega información del proceso a process_info
    process_info[message.chat.id] = {
        "file": downloaded_file,
        "original_size": original_size,
        "start_time": None,
        "end_time": None,
    }

    # Inicia el proceso de compresión/descompresión/picado
    await message.reply_text(
        "Proceso iniciado, espera a que termine.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Cancelar", callback_data="cancel")]]
        )
    )
    task_queue.put((message.chat.id, downloaded_file, None))

@app.on_message(filters.command(["comprimir"]))
async def compress_command(client, message):
    if is_group_banned(message.chat.id):
        await message.reply_text("Este grupo está bloqueado del bot.")
        return
    await message.reply_text("Envíame el archivo para comprimir.")

@app.on_message(filters.command(["descomprimir"]))
async def uncompress_command(client, message):
    if is_group_banned(message.chat.id):
        await message.reply_text("Este grupo está bloqueado del bot.")
        return
    await message.reply_text("Envíame el archivo para descomprimir.")

@app.on_message(filters.command(["picar"]))
async def split_command(client, message):
    if is_group_banned(message.chat.id):
        await message.reply_text("Este grupo está bloqueado del bot.")
        return
    try:
        size = int(message.text.split(" ")[1]) # Obtiene el tamaño de la parte en segundos
        await message.reply_text("Envíame el video para picar.")
    except IndexError:
        await message.reply_text("Por favor, especifica el tamaño de la parte en segundos.")
        return
    except ValueError:
        await message.reply_text("El tamaño de la parte debe ser un número.")
        return

# Ejecuta el bot
app.run()
