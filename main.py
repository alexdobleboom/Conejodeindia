import os
import subprocess
import datetime
import zipfile
import shutil
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import PeerIdInvalid, ChatAdminRequired, UserNotParticipant, ChatInvalid

# Configuraciones
api_id = 24288670  # Reemplaza con tu api_id
api_hash = '81c58005802498656d6b689dae1edacc'  # Reemplaza con tu api_hash
bot_token = '7507770865:AAFDQ0Lbuo5Ca-mTnqSa-dK_UJENs5B2v1Q'  # Reemplaza con tu token del bot

# Listas de usuarios
admin_list = ['TheDemonsuprem', 'username2', 'username3']  # Lista de administradores
user_list = ['TheDemonsuprem', 'username2', 'username3']  # Lista de usuarios permitidos
group_list = []  # Lista de grupos permitidos
banned_users = []  # Lista de usuarios baneados
superadmin_list = ['TheDemonsuprem', 'username2'] # Lista de administradores supremos

# Configuraciones de compresión predeterminadas
default_resolution = '740x480'
default_crf = '32'
default_audio_bitrate = '60k'
default_fps = '18'
default_preset = 'ultrafast'
default_codec = 'libx264'

# Límite de tamaño de archivo predeterminado
max_file_size = 1024 * 1024 * 1024  # 1 GB

# Información del Bot
bot_version = '2.0.0'
bot_creator = 'The Big Boss'
bot_creation_date = '2024-11-2'

# Crea el cliente de Pyrogram
app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Función para verificar autorización
def is_user_authorized(username):
    return username in admin_list or username in user_list or username in group_list

# Función para verificar autorización de superadmin
def is_superadmin(username):
    return username in superadmin_list

# Función para obtener la ID de un usuario
async def get_user_id(client, username):
    try:
        user = await client.get_users(username)
        return user.id
    except PeerIdInvalid:
        return None

# Función para obtener la ID de un grupo
async def get_group_id(client, group_id):
    try:
        group = await client.get_chat(group_id)
        return group.id
    except ChatInvalid:
        return None

# Función para enviar un mensaje de advertencia a los administradores
async def warn_admins(client, message: Message, reason):
    for admin in admin_list:
        try:
            await client.send_message(chat_id=await get_user_id(client, admin), text=f"🚨¡Alerta!🚨\n\nUsuario: @{message.from_user.username} ({message.from_user.id})\nIntento de acción no autorizada: {reason}")
        except Exception as e:
            print(f"Error al enviar advertencia a {admin}: {e}")

# Comando para añadir un usuario al bot
@app.on_message(filters.command("add"))
async def add_user(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"

    if not is_superadmin(username):
        await warn_admins(client, message, "Intento de agregar usuario")
        await app.send_message(chat_id=message.chat.id, text="❌No tienes permiso para usar este comando❌.")
        return

    if len(message.command) > 1:
        new_username = message.command[1]
        if new_username not in banned_users:
            user_list.append(new_username)
            await app.send_message(chat_id=message.chat.id, text=f"✅Usuario {new_username} añadido correctamente✅.")
        else:
            await app.send_message(chat_id=message.chat.id, text=f"❌El usuario {new_username} está baneado❌.")
    else:
        await app.send_message(chat_id=message.chat.id, text="Formato incorrecto. Usa /add @username.")

# Comando para banear un usuario del bot
@app.on_message(filters.command("ban"))
async def ban_user(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"

    if not is_superadmin(username):
        await warn_admins(client, message, "Intento de banear usuario")
        await app.send_message(chat_id=message.chat.id, text="❌No tienes permiso para usar este comando❌.")
        return

    if len(message.command) > 1:
        banned_username = message.command[1]
        if banned_username in user_list:
            user_list.remove(banned_username)
            banned_users.append(banned_username)  # Agregar a la lista de usuarios baneados
            await app.send_message(chat_id=message.chat.id, text=f"✅Usuario {banned_username} baneado correctamente✅.")
        elif banned_username in admin_list and not is_superadmin(banned_username):  # Solo superadmin puede banear a admin
            admin_list.remove(banned_username)
            banned_users.append(banned_username)  # Agregar a la lista de usuarios baneados
            await app.send_message(chat_id=message.chat.id, text=f"✅Administrador {banned_username} baneado correctamente✅.")
        else:
            await app.send_message(chat_id=message.chat.id, text=f"❌El usuario {banned_username} no está en la lista de usuarios❌.")
    else:
        await app.send_message(chat_id=message.chat.id, text="Formato incorrecto. Usa /ban @username.")

# Comando para listar archivos subidos
@app.on_message(filters.command("ls"))
async def list_files(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"

    if not is_superadmin(username):
        await warn_admins(client, message, "Intento de ver la lista de archivos")
        await app.send_message(chat_id=message.chat.id, text="❌No tienes permiso para usar este comando❌.")
        return

    # Directorio donde se almacenan los archivos subidos
    upload_dir = 'uploads'  # Puedes cambiar este nombre si es necesario
    os.makedirs(upload_dir, exist_ok=True)

    files_list = []
    for filename in os.listdir(upload_dir):
        filepath = os.path.join(upload_dir, filename)
        if os.path.isfile(filepath):
            size = os.path.getsize(filepath) // (1024 * 1024)  # Tamaño en MB
            files_list.append(f" - {filename}: {size} MB")

    if files_list:
        await app.send_message(chat_id=message.chat.id, text=f"Lista de archivos:\n{os.linesep.join(files_list)}")
    else:
        await app.send_message(chat_id=message.chat.id, text="No se encontraron archivos.")

# Comando para cambiar la calidad de compresión
@app.on_message(filters.command("calidad"))
async def change_quality(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"

    if len(message.command) > 1:
        quality_settings = message.command[1].split(' ')
        for setting in quality_settings:
            key, value = setting.split('=')
            if key == 'resolution':
                global default_resolution
                default_resolution = value
            elif key == 'crf':
                global default_crf
                default_crf = value
            elif key == 'audio_bitrate':
                global default_audio_bitrate
                default_audio_bitrate = value
            elif key == 'fps':
                global default_fps
                default_fps = value
            elif key == 'preset':
                global default_preset
                default_preset = value
            elif key == 'codec':
                global default_codec
                default_codec = value
            else:
                await app.send_message(chat_id=message.chat.id, text="Parámetro inválido.")
                return

        await app.send_message(chat_id=message.chat.id, text="✅Calidad de compresión actualizada✅.")
    else:
        await app.send_message(chat_id=message.chat.id, text="Formato incorrecto. Usa /calidad resolution=640x480 crf=32 audio_bitrate=60k fps=18 preset=veryfast codec=libx264.")

# Comando para obtener la ID de un usuario
@app.on_message(filters.command("id"))
async def get_user_id_command(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"

    if len(message.command) > 1:
        target_username = message.command[1]
        user_id = await get_user_id(client, target_username)
        if user_id:
            await app.send_message(chat_id=message.chat.id, text=f"La ID de {target_username} es: {user_id}")
        else:
            await app.send_message(chat_id=message.chat.id, text="❌Usuario no encontrado❌.")
    else:
        await app.send_message(chat_id=message.chat.id, text="Formato incorrecto. Usa /id @username.")

# Comando para enviar información a los usuarios
@app.on_message(filters.command("info"))
async def send_info(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"

    if not is_superadmin(username):
        await warn_admins(client, message, "Intento de enviar información a los usuarios")
        await app.send_message(chat_id=message.chat.id, text="❌No tienes permiso para usar este comando❌.")
        return

    if len(message.command) > 1:
        info_message = " ".join(message.command[1:])
        for user in user_list:
            try:
                await app.send_message(chat_id=await get_user_id(client, user), text=info_message)
            except Exception as e:
                print(f"Error al enviar información a {user}: {e}")

        await app.send_message(chat_id=message.chat.id, text="✅Información enviada correctamente a todos los usuarios✅.")
    else:
        await app.send_message(chat_id=message.chat.id, text="Formato incorrecto. Usa /info [mensaje]")

# Comando para listar administradores
@app.on_message(filters.command("listadmin"))
async def list_admins(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"

    if not is_user_authorized(username):
        await app.send_message(chat_id=message.chat.id, text="❌No tienes permiso para usar este comando❌.")
        return

    if admin_list:
        await app.send_message(chat_id=message.chat.id, text=f"Lista de administradores:\n{os.linesep.join(admin_list)}")
    else:
        await app.send_message(chat_id=message.chat.id, text="No hay administradores registrados.")

# Comando para listar usuarios
@app.on_message(filters.command("listuser"))
async def list_users(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"

    if not is_user_authorized(username):
        await app.send_message(chat_id=message.chat.id, text="❌No tienes permiso para usar este comando❌.")
        return

    if user_list:
        await app.send_message(chat_id=message.chat.id, text=f"Lista de usuarios:\n{os.linesep.join(user_list)}")
    else:
        await app.send_message(chat_id=message.chat.id, text="No hay usuarios registrados.")

# Comando para listar grupos
@app.on_message(filters.command("listgrup"))
async def list_groups(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"

    if not is_user_authorized(username):
        await app.send_message(chat_id=message.chat.id, text="❌No tienes permiso para usar este comando❌.")
        return

    if group_list:
        await app.send_message(chat_id=message.chat.id, text=f"Lista de grupos:\n{os.linesep.join(group_list)}")
    else:
        await app.send_message(chat_id=message.chat.id, text="No hay grupos registrados.")

# Comando para agregar un grupo
@app.on_message(filters.command("grup"))
async def add_group(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"

    if not is_superadmin(username):
        await warn_admins(client, message, "Intento de agregar un grupo")
        await app.send_message(chat_id=message.chat.id, text="❌No tienes permiso para usar este comando❌.")
        return

    if len(message.command) > 1:
        group_id = message.command[1]
        group_id = await get_group_id(client, group_id)
        if group_id:
            group_list.append(group_id)
            await app.send_message(chat_id=message.chat.id, text=f"✅Grupo con ID {group_id} agregado correctamente✅.")
        else:
            await app.send_message(chat_id=message.chat.id, text="❌Grupo no encontrado❌.")
    else:
        await app.send_message(chat_id=message.chat.id, text="Formato incorrecto. Usa /grup [ID del grupo].")

# Comando para listar usuarios baneados
@app.on_message(filters.command("listban"))
async def list_banned_users(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"

    if not is_user_authorized(username):
        await app.send_message(chat_id=message.chat.id, text="❌No tienes permiso para usar este comando❌.")
        return

    if banned_users:
        await app.send_message(chat_id=message.chat.id, text=f"Lista de usuarios baneados:\n{os.linesep.join(banned_users)}")
    else:
        await app.send_message(chat_id=message.chat.id, text="No hay usuarios baneados.")

# Comando para cambiar el límite de tamaño de archivo
@app.on_message(filters.command("max"))
async def change_max_file_size(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"

    if not is_superadmin(username):
        await warn_admins(client, message, "Intento de cambiar el límite de tamaño de archivo")
        await app.send_message(chat_id=message.chat.id, text="❌No tienes permiso para usar este comando❌.")
        return

    if len(message.command) > 1:
        try:
            new_max_size_str = message.command[1]
            new_max_size_str = new_max_size_str.upper()

            if new_max_size_str[-1] == 'K':
                new_max_size = int(new_max_size_str[:-1]) * 1024
            elif new_max_size_str[-1] == 'M':
                new_max_size = int(new_max_size_str[:-1]) * 1024 * 1024
            elif new_max_size_str[-1] == 'G':
                new_max_size = int(new_max_size_str[:-1]) * 1024 * 1024 * 1024
            else:
                new_max_size = int(new_max_size_str)

            global max_file_size
            max_file_size = new_max_size
            await app.send_message(chat_id=message.chat.id, text=f"✅Límite de tamaño de archivo actualizado a {new_max_size_str}B✅.")
        except ValueError:
            await app.send_message(chat_id=message.chat.id, text="Formato incorrecto. Usa /max [tamaño]B (K, M, G).")
    else:
        await app.send_message(chat_id=message.chat.id, text="Formato incorrecto. Usa /max [tamaño]B (K, M, G).")

# Comando /start
@app.on_message(filters.command("start"))
async def start_handler(client, message: Message):
    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("Canal del Bot", url="https://t.me/tu_canal"),
            InlineKeyboardButton("Programador", url=f"https://t.me/{bot_creator}")
        ]]
    )
    await app.send_message(chat_id=message.chat.id, 
                           text=f"¡Hola! 👋 Soy un bot que puede comprimir videos, descomprimir archivos ZIP y dividir archivos en partes.\n\nUsa los siguientes comandos: \n/compress - Comprime un video\n/descompress - Descomprime un archivo ZIP\n/picarzip - Divide un archivo en partes.",
                           reply_markup=keyboard)

# Comando /help
@app.on_message(filters.command("help"))
async def help_handler(client, message: Message):
    await app.send_message(chat_id=message.chat.id, 
                           text="**Comandos disponibles:**\n\n"
                                "**Comandos de administración:**\n"
                                " - /add @username: Agrega un usuario al bot.\n"
                                " - /ban @username: Banea un usuario del bot.\n"
                                " - /ls: Muestra la lista de archivos subidos.\n"
                                " - /calidad [settings]: Cambia la calidad de compresión (resolution=640x480 crf=32 audio_bitrate=60k fps=18 preset=veryfast codec=libx264).\n"
                                " - /max [tamaño]B: Cambia el límite de tamaño de archivo (K, M, G).\n"
                                " - /listadmin: Muestra la lista de administradores.\n"
                                " - /listuser: Muestra la lista de usuarios.\n"
                                " - /listgrup: Muestra la lista de grupos.\n"
                                " - /grup [ID del grupo]: Agrega un grupo al bot.\n"
                                " - /listban: Muestra la lista de usuarios baneados.\n"
                                " - /info [mensaje]: Envía un mensaje a todos los usuarios.\n\n"
                                "**Comandos generales:**\n"
                                " - /compress: Comprime un video.\n"
                                " - /descompress: Descomprime un archivo ZIP.\n"
                                " - /picarzip: Divide un archivo en partes.\n"
                                " - /id @username: Obtiene la ID de un usuario.\n"
                                " - /about: Muestra información sobre el bot.\n\n"
                                "**Ejemplo de uso:**\n"
                                " - /compress (responde a un video para comprimirlo)\n"
                                " - /calidad resolution=1280x720 crf=28 audio_bitrate=128k fps=24 preset=medium codec=libx265\n"
                                " - /max 5GB\n"
                                " - /add @tu_usuario\n"
                                " - /ban @usuario_a_banear\n"
                                " - /grup -1001234567890", 
                           disable_web_page_preview=True)

# Comando /about
@app.on_message(filters.command("about"))
async def about_handler(client, message: Message):
    await app.send_message(chat_id=message.chat.id, 
                           text=f"🤖 **Acerca del bot:**\n\n"
                                f" - Versión: {bot_version}\n"
                                f" - Creador: {bot_creator}\n"
                                f" - Fecha de creación: {bot_creation_date}\n"
                                f" - Funciones: Comprimir videos, descomprimir archivos ZIP, dividir archivos en partes.\n\n"
                                f"¡Espero que te sea útil! 🤗", 
                           disable_web_page_preview=True)

# Maneja los mensajes de los usuarios que no son administradores y usan comandos de administración
@app.on_message(filters.command(["add", "ban", "ls", "calidad", "max", "grup", "info", "listban", "listadmin", "listuser", "listgrup"]))
async def unauthorized_admin_command(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"

    if not is_superadmin(username):
        await warn_admins(client, message, f"Intento de usar comando de administración: {message.command[0]}")
        await app.send_message(chat_id=message.chat.id, text="❌No tienes permiso para usar este comando❌.")

# Elimina los mensajes anteriores al finalizar el proceso
@app.on_message(filters.command(["compress", "descompress", "picarzip"]))
async def process_completed(client, message: Message):
    if message.reply_to_message:
        await message.reply_to_message.delete()
    await message.delete()

# Comando para comprimir videos
@app.on_message(filters.command("compress"))
async def compress_video(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"

    if message.reply_to_message and message.reply_to_message.video:
        original_video_path = await app.download_media(message.reply_to_message.video)
        original_size = os.path.getsize(original_video_path)

        if original_size > max_file_size:
            await app.send_message(chat_id=message.chat.id, text=f"❌El video es demasiado grande. El límite es {max_file_size // (1024 * 1024)} MB❌.")
            return

        await app.send_message(chat_id=message.chat.id, text="🚫Proceso iniciado espere a que termine🚫.")

        compressed_video_path = f"{os.path.splitext(original_video_path)[0]}_compressed.mkv"
        ffmpeg_command = [
            'ffmpeg', '-y', '-i', original_video_path,
            '-s', default_resolution, '-crf', default_crf,
            '-b:a', default_audio_bitrate,
            '-preset', default_preset,
            '-c:v', default_codec,
            compressed_video_path
        ]

        try:
            start_time = datetime.datetime.now()
            process = subprocess.Popen(ffmpeg_command, stderr=subprocess.PIPE, text=True)
            await app.send_message(chat_id=message.chat.id, text="↗️En Progreso...↘️")

            while True:
                output = process.stderr.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())

            # Recuperar tamaño y duración
            compressed_size = os.path.getsize(compressed_video_path)
            duration = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries",
                                                 "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
                                                 compressed_video_path])
            duration = float(duration.strip())
            duration_str = str(datetime.timedelta(seconds=duration))

            processing_time = datetime.datetime.now() - start_time
            processing_time_str = str(processing_time).split('.')[0]  # Formato sin microsegundos

            # Descripción para el video comprimido
            description = (
                f"꧁༺ Proceso Finalizado ༻꧂\n"
                f"⏬ Peso Original: {original_size // (1024 * 1024)} MB\n"
                f"⏫ Peso Procesado: {compressed_size // (1024 * 1024)} MB\n"
                f"▶️ Tiempo de Procesamiento: {processing_time_str}\n"
                f"🎦 Tiempo del Video: {duration_str}\n"
                f"🎉 ¡Que lo disfrute!🎊"
            )

            # Enviar el video comprimido con la descripción
            await app.send_document(chat_id=message.chat.id, document=compressed_video_path, caption=description)

        except Exception as e:
            await app.send_message(chat_id=message.chat.id, text=f"⭕Ocurrió un error en el video⭕: {e}")
        finally:
            if os.path.exists(original_video_path):
                os.remove(original_video_path)
            if os.path.exists(compressed_video_path):
                os.remove(compressed_video_path)
    else:
        await app.send_message(chat_id=message.chat.id, text="‼️Responde a un video para comprimirlo‼️.")

# Comando para descomprimir archivos ZIP
@app.on_message(filters.command("descompress"))
async def decompress_file(client, message: Message):
    if message.reply_to_message and message.reply_to_message.document:
        archive_path = await app.download_media(message.reply_to_message.document)
        file_extension = os.path.splitext(archive_path)[1].lower()
        extract_folder = "extracted_files"

        if file_extension != '.zip':
            await app.send_message(chat_id=message.chat.id, text="El formato del archivo debe de ser 👉.zip.")
            return

        os.makedirs(extract_folder, exist_ok=True)
        await app.send_message(chat_id=message.chat.id, text="↗️En Progreso...↘️")

        try:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_folder)

            await app.send_message(chat_id=message.chat.id, text="😁Finalizado😁.")
            for file in os.listdir(extract_folder):
                await app.send_document(chat_id=message.chat.id, document=os.path.join(extract_folder, file))

        except Exception as e:
            await app.send_message(chat_id=message.chat.id, text=f"⭕Error al descomprimir el archivo⭕: {e}")
        finally:
            if os.path.exists(archive_path):
                os.remove(archive_path)

            shutil.rmtree(extract_folder)  # Elimina el folder de extracción
    else:
        await app.send_message(chat_id=message.chat.id, text="‼️Responde a un archivo .zip ‼️.")

# Comando para dividir archivos en partes
@app.on_message(filters.command("picarzip"))
async def split_file(client, message: Message):
    if message.reply_to_message and message.reply_to_message.document:
        file_path = await app.download_media(message.reply_to_message.document)
        parts_list = []
        part_sizes = [5 * 1024 * 1024, 15 * 1024 * 1024, 25 * 1024 * 1024, 50 * 1024 * 1024, 100 * 1024 * 1024]  # Tamaños en bytes

        await app.send_message(chat_id=message.chat.id, text="↗️Proceso en marcha...↘️")
        file_size = os.path.getsize(file_path)
        part_num = 1

        while file_size > 0:
            size = min(part_sizes[-1], file_size)  # Usar el tamaño máximo definido
            part_filename = f"{file_path}.part{part_num}"

            with open(part_filename, 'wb') as part_file:
                with open(file_path, 'rb') as original_file:
                    part_file.write(original_file.read(size))

            parts_list.append(part_filename)
            file_size -= size
            part_num += 1

        for part in parts_list:
            await app.send_document(chat_id=message.chat.id, document=part)
            os.remove(part)

        await app.send_message(chat_id=message.chat.id, text="Completado👌.")
        os.remove(file_path)  # Eliminar el archivo original después de dividir
    else:
        await app.send_message(chat_id=message.chat.id, text="‼️Responde a un archivo para dividirlo‼️.")

# Inicia el bot
app.run()
