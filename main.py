import os
import subprocess
import datetime
import zipfile
import shutil

import pyrogram
from pyrogram import Client, filters, Message
from pyrogram.types import Message, Chat, InlineKeyboardMarkup, InlineKeyboardButton

# Configuración
api_id = 24288670
api_hash = "81c58005802498656d6b689dae1edacc"
bot_token = "7507770865:AAFDQ0Lbuo5Ca-mTnqSa-dK_UJENs5B2v1Q"

# Límites y configuraciones predeterminadas
max_file_size = 1024 * 1024 * 1024 * 5 # 5 GB
default_resolution = "720x480"
default_crf = "23"
default_audio_bitrate = "128k"
default_preset = "ultrafast"
default_codec = "libx264"

# Listas de usuarios, administradores y grupos
admin_list = ['TheDemonsuprem'] # Lista de administradores
user_list = ['TheDemonsuprem', 'Sasuke286', 'Shadow_Eminencie'] # Lista de usuarios permitidos
group_list = [] # Lista de grupos permitidos
banned_users = [] # Lista de usuarios baneados
superadmin_list = ['TheDemonsuprem'] # Lista de administradores supremos

# Función para verificar si un usuario es administrador
def is_admin(user_id):
    return user_id in admin_list or user_id in superadmin_list

# Función para verificar si un usuario es administrador supremo
def is_superadmin(user_id):
    return user_id in superadmin_list

# Función para obtener la ID de un usuario
def get_user_id(username):
    try:
        user = app.get_users(username)
        return user.id
    except Exception as e:
        print(f"Error al obtener la ID del usuario: {e}")
        return None

# Función para obtener la ID de un grupo
def get_group_id(group_link):
    try:
        group = app.get_chat(group_link)
        return group.id
    except Exception as e:
        print(f"Error al obtener la ID del grupo: {e}")
        return None

# Función para comprimir video
def compress_video(original_video_path, compressed_video_path, resolution, crf, audio_bitrate, preset, codec):
    ffmpeg_command = [
        'ffmpeg', '-y', '-i', original_video_path,
        '-s', resolution, '-crf', crf,
        '-b:a', audio_bitrate,
        '-preset', preset,
        '-c:v', codec,
        compressed_video_path
    ]
    try:
        process = subprocess.Popen(ffmpeg_command, stderr=subprocess.PIPE, text=True)
        while True:
            output = process.stderr.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        return True
    except Exception as e:
        print(f"Error al comprimir el video: {e}")
        return False

# Función para enviar un mensaje de error
async def send_error_message(client, message, error_text):
    await client.send_message(chat_id=message.chat.id, text=f"❌Error: {error_text}❌")

# Función para enviar un mensaje de éxito
async def send_success_message(client, message, success_text):
    await client.send_message(chat_id=message.chat.id, text=f"✅Exito: {success_text}✅")

# Función para notificar al administrador supremo
async def notify_superadmin(client, message, reason):
    for superadmin_id in superadmin_list:
        await client.send_message(chat_id=superadmin_id, text=f"⚠️Alerta⚠️: {reason}")
        await client.pin_message(chat_id=superadmin_id, message_id=message.message_id)

# Función para verificar la seguridad
async def check_security(client, message):
    user_id = message.from_user.id
    # Verifica si el usuario está baneado
    if user_id in banned_users:
        await send_error_message(client, message, "Estás bloqueado de este bot.")
        return False
    # Verifica si el usuario tiene acceso
    if user_id not in user_list and user_id not in admin_list and user_id not in superadmin_list:
        await send_error_message(client, message, "No tienes acceso a este bot.")
        await notify_superadmin(client, message, f"Usuario @{message.from_user.username} (ID: {user_id}) intentó acceder al bot sin autorización.")
        return False
    # Verifica si el usuario está intentando usar un comando de administrador
    if not is_admin(user_id) and message.text.startswith(("/add", "/ban", "/addadmin", "/banadmin", "/grup", "/bangrup", "/listuser", "/listadmin", "/listgrup", "/banlist", "/max", "/infouser")):
        await send_error_message(client, message, "No tienes permisos para usar este comando.")
        await notify_superadmin(client, message, f"Usuario @{message.from_user.username} (ID: {user_id}) intentó usar un comando de administrador sin autorización.")
        return False
    return True

app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

@app.on_message(filters.command(["start"]))
async def start(client, message):
    user_id = message.from_user.id
    if await check_security(client, message):
        inline_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("𝑪𝑨𝑵𝑨𝑳 𝑶𝑭𝑰𝑪𝑰𝑨𝑳 ©️", url="https://t.me/AnimalProjets"),
                    InlineKeyboardButton("𝑷𝑹𝑶𝑮𝑹𝑨𝑴𝑨𝑫𝑶𝑹 👨‍💻", url="t.me/TheDemonsuprem")
                ]
            ]
        )
        await message.reply_text("👋 Bienvenido a 🦊 FOX VIP COMPRESS 📚", reply_markup=inline_markup)

@app.on_message(filters.command("help"))
async def help_handler(client, message: Message):
    user_id = message.from_user.id
    if await check_security(client, message):
        help_text = "Comandos disponibles:\n"
        if is_admin(user_id):
            help_text += f" - /add @username: Agrega un usuario al bot. ➕\n"
            help_text += f" - /ban @username: Bloquea un usuario del bot. 🚫\n"
            help_text += f" - /addadmin @username: Promueve a un usuario a administrador. 👮‍♂️\n"
            help_text += f" - /banadmin @username: Revoca los permisos de administrador. 👮‍♀️\n"
            help_text += f" - /grup ID/enlace: Agrega un grupo al bot. 👥\n"
            help_text += f" - /bangrup ID/enlace: Bloquea un grupo del bot. 🚫\n"
            help_text += f" - /listuser: Muestra los usuarios del bot. 👥\n"
            help_text += f" - /listadmin: Muestra los administradores del bot. 👮‍♂️\n"
            help_text += f" - /listgrup: Muestra los grupos del bot. 👥\n"
            help_text += f" - /banlist: Muestra los usuarios bloqueados del bot. 🚫\n"
            help_text += f" - /infouser [Mensaje]: Envía un mensaje a los usuarios y grupos del bot. 📢\n"
        if is_superadmin(user_id):
            help_text += f" - /max tamaño: Cambia el límite de tamaño de los videos (solo admin supremo). 📈\n"
        help_text += f" - /calidad resolution=valor crf=valor audio_bitrate=valor fps=valor preset=valor codec=valor: Ajusta la configuración de compresión. ⚙️\n"
        help_text += f" - /convert: Comprime un video. 🎥\n"
        help_text += f" - /descompress: Descomprime un archivo ZIP. 📦\n"
        help_text += f" - /picarzip: Divide un archivo en partes. ✂️\n"
        help_text += f" - /extract_audio: Extrae el audio de un video. 🎶\n"
        help_text += f" - /id @username: Obtiene la ID de un usuario. 🆔\n"
        help_text += f" - /soport [Mensaje]: Envía un mensaje al administrador supremo. 📩\n"
        help_text += f" - /about: Da información sobre el bot. ℹ️\n"
        await client.send_message(chat_id=message.chat.id, text=help_text)

@app.on_message(filters.command("add") & filters.user(admin_list + superadmin_list))
async def add_user_handler(client, message: Message):
    if await check_security(client, message):
        username = message.text.split(" ")[1]
        user_id = get_user_id(username)
        if user_id is not None:
            if user_id not in user_list:
                user_list.append(user_id)
                await send_success_message(client, message, f"Usuario @{username} agregado al bot. 👍")
            else:
                await send_error_message(client, message, f"El usuario @{username} ya está en la lista. 😕")
        else:
            await send_error_message(client, message, f"No se pudo encontrar el usuario @{username}. 🕵️‍♂️")

@app.on_message(filters.command("ban") & filters.user(admin_list + superadmin_list))
async def ban_user_handler(client, message: Message):
    if await check_security(client, message):
        username = message.text.split(" ")[1]
        user_id = get_user_id(username)
        if user_id is not None:
            if user_id in user_list:
                user_list.remove(user_id)
                banned_users.append(user_id)
                await send_success_message(client, message, f"Usuario @{username} bloqueado del bot. 🚫")
            else:
                await send_error_message(client, message, f"El usuario @{username} no está en la lista. 🤔")
        else:
            await send_error_message(client, message, f"No se pudo encontrar el usuario @{username}. 🕵️‍♂️")

@app.on_message(filters.command("addadmin") & filters.user(superadmin_list))
async def add_admin_handler(client, message: Message):
    if await check_security(client, message):
        username = message.text.split(" ")[1]
        user_id = get_user_id(username)
        if user_id is not None:
            if user_id not in admin_list:
                admin_list.append(user_id)
                await send_success_message(client, message, f"Usuario @{username} promovido a administrador. 👮‍♂️")
            else:
                await send_error_message(client, message, f"El usuario @{username} ya es administrador. 👮‍♂️")
        else:
            await send_error_message(client, message, f"No se pudo encontrar el usuario @{username}. 🕵️‍♂️")

@app.on_message(filters.command("banadmin") & filters.user(superadmin_list))
async def ban_admin_handler(client, message: Message):
    if await check_security(client, message):
        username = message.text.split(" ")[1]
        user_id = get_user_id(username)
        if user_id is not None:
            if user_id in admin_list:
                admin_list.remove(user_id)
                await send_success_message(client, message, f"Usuario @{username} perdió los permisos de administrador. 👮‍♀️")
            else:
                await send_error_message(client, message, f"El usuario @{username} no es administrador. 👮‍♀️")
        else:
            await send_error_message(client, message, f"No se pudo encontrar el usuario @{username}. 🕵️‍♂️")

@app.on_message(filters.command("grup") & filters.user(admin_list + superadmin_list))
async def add_group_handler(client, message: Message):
    if await check_security(client, message):
        group_id = message.text.split(" ")[1]
        try:
            group_id = int(group_id) # Si es un ID numérico
        except ValueError:
            group_id = get_group_id(group_id) # Si es un enlace
        if group_id is not None:
            if group_id not in group_list:
                group_list.append(group_id)
                await send_success_message(client, message, f"Grupo con ID {group_id} agregado al bot. 👥")
            else:
                await send_error_message(client, message, f"El grupo con ID {group_id} ya está en la lista. 👥")
        else:
            await send_error_message(client, message, f"No se pudo encontrar el grupo. 🕵️‍♂️")

@app.on_message(filters.command("bangrup") & filters.user(admin_list + superadmin_list))
async def ban_group_handler(client, message: Message):
    if await check_security(client, message):
        group_id = message.text.split(" ")[1]
        try:
            group_id = int(group_id) # Si es un ID numérico
        except ValueError:
            group_id = get_group_id(group_id) # Si es un enlace
        if group_id is not None:
            if group_id in group_list:
                group_list.remove(group_id)
                banned_groups.append(group_id)
                await send_success_message(client, message, f"Grupo con ID {group_id} bloqueado del bot. 🚫")
            else:
                await send_error_message(client, message, f"El grupo con ID {group_id} no está en la lista. 🤔")
        else:
            await send_error_message(client, message, f"No se pudo encontrar el grupo. 🕵️‍♂️")

@app.on_message(filters.command("max") & filters.user(superadmin_list))
async def set_max_size_handler(client, message: Message):
    if await check_security(client, message):
        try:
            size_gb = int(message.text.split(" ")[1])
            global max_file_size
            max_file_size = size_gb * 1024 * 1024 * 1024
            await send_success_message(client, message, f"El límite de tamaño de los videos se ha establecido a {size_gb} GB. 📈")
        except Exception as e:
            await send_error_message(client, message, f"Error al establecer el límite de tamaño: {e}")

@app.on_message(filters.command("calidad"))
async def set_quality_handler(client, message: Message):
    if await check_security(client, message):
        global default_resolution, default_crf, default_audio_bitrate, default_preset, default_codec
        try:
            quality_settings = message.text.split(" ")[1]
            settings_dict = {}
            for setting in quality_settings.split(" "):
                key, value = setting.split("=")
                settings_dict[key] = value
            if "resolution" in settings_dict:
                default_resolution = settings_dict["resolution"]
            if "crf" in settings_dict:
                default_crf = settings_dict["crf"]
            if "audio_bitrate" in settings_dict:
                default_audio_bitrate = settings_dict["audio_bitrate"]
            if "preset" in settings_dict:
                default_preset = settings_dict["preset"]
            if "codec" in settings_dict:
                default_codec = settings_dict["codec"]
            await send_success_message(client, message, "La calidad de compresión se ha actualizado. 👌")
        except Exception as e:
            await send_error_message(client, message, f"Error al actualizar la calidad de compresión: {e}")

@app.on_message(filters.command("convert") & filters.user(user_list + admin_list + superadmin_list))
async def compress_video(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"
    if message.reply_to_message and message.reply_to_message.video:
        original_video_path = await app.download_media(message.reply_to_message.video)
        original_size = os.path.getsize(original_video_path)

        if original_size > max_file_size:
            await app.send_message(chat_id=message.chat.id, text=f"❌El video es muy grande. Supera los {max_file_size // (1024 * 1024)} MB❌.")
            return

        await app.send_message(chat_id=message.chat.id, text="🚫Proceso iniciado espera a que termine🚫.")

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
            await app.send_message(chat_id=message.chat.id, text="↗️En Proceso...↘️")

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
            processing_time_str = str(processing_time).split('.')[0] # Formato sin microsegundos

            # Descripción para el video comprimido
            description = (
                f"✅¡Proceso finalizado! 🎥\n"
                f"⇓ Peso Original: {original_size // (1024 * 1024)} MB\n"
                f"⇑ Peso Procesado: {compressed_size // (1024 * 1024)} MB\n"
                f"⏳ Tiempo de Procesamiento: {processing_time_str}\n"
                f"⏱ Tiempo del Video: {duration_str}\n"
                f"¡Que lo disfrutes! 😊"
            )

            # Enviar el video comprimido con la descripción
            await app.send_document(chat_id=message.chat.id, document=compressed_video_path, caption=description)

        except Exception as e:
            await app.send_message(chat_id=message.chat.id, text=f"⭕Ocurrio un error: {e} ⭕")
        finally:
            if os.path.exists(original_video_path):
                os.remove(original_video_path)
            if os.path.exists(compressed_video_path):
                os.remove(compressed_video_path)
    else:
        await app.send_message(chat_id=message.chat.id, text="‼️Responde a un video‼️.")

@app.on_message(filters.command("descompress") & filters.user(user_list + admin_list + superadmin_list))
async def decompress_file(client, message: Message):
    if message.reply_to_message and message.reply_to_message.document:
        archive_path = await app.download_media(message.reply_to_message.document)
        file_extension = os.path.splitext(archive_path)[1].lower()
        extract_folder = "extracted_files"

        if file_extension != '.zip':
            await app.send_message(chat_id=message.chat.id, text="‼️El formato del archivo debe ser 👉.zip‼️.")
            return

        os.makedirs(extract_folder, exist_ok=True)
        await app.send_message(chat_id=message.chat.id, text="↗️En Marcha...↘️")

        try:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_folder)

            await app.send_message(chat_id=message.chat.id, text="😁Finalizado😁.")
            for file in os.listdir(extract_folder):
                await app.send_document(chat_id=message.chat.id, document=os.path.join(extract_folder, file))

        except Exception as e:
            await app.send_message(chat_id=message.chat.id, text=f"⭕Ocurrio un error: {e} ⭕")
        finally:
            if os.path.exists(archive_path):
                os.remove(archive_path)

            shutil.rmtree(extract_folder) # Elimina el folder de extracción
    else:
        await app.send_message(chat_id=message.chat.id, text="‼️Responde a un .zip ‼️.")

@app.on_message(filters.command("picarzip") & filters.user(user_list + admin_list + superadmin_list))
async def split_file(client, message: Message):
    if message.reply_to_message and message.reply_to_message.document:
        file_path = await app.download_media(message.reply_to_message.document)
        parts_list = []
        part_sizes = [5 * 1024 * 1024, 15 * 1024 * 1024, 25 * 1024 * 1024, 50 * 1024 * 1024, 100 * 1024 * 1024] # Tamaños en bytes

        await app.send_message(chat_id=message.chat.id, text="↗️Proceso iniciado...↘️")
        file_size = os.path.getsize(file_path)
        part_num = 1

        while file_size > 0:
            size = min(part_sizes[-1], file_size) # Usar el tamaño máximo definido
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

        await app.send_message(chat_id=message.chat.id, text="✅¡Proceso finalizado! ✂️ ")
        os.remove(file_path) # Eliminar el archivo original después de dividir
    else:
        await app.send_message(chat_id=message.chat.id, text="‼️Responde a un archivo‼️.")

@app.on_message(filters.command("extract_audio") & filters.user(user_list + admin_list + superadmin_list))
async def extract_audio(client, message: Message):
    if message.reply_to_message and message.reply_to_message.video:
        video_path = await app.download_media(message.reply_to_message.video)
        audio_path = f"{os.path.splitext(video_path)[0]}.mp3"

        ffmpeg_command = [
            'ffmpeg', '-y', '-i', video_path,
            '-vn', # Deshabilitar el video
            '-acodec', 'libmp3lame', # Codificador de audio
            audio_path
        ]

        try:
            subprocess.run(ffmpeg_command, stderr=subprocess.PIPE, check=True)
            await app.send_audio(chat_id=message.chat.id, audio=audio_path, caption="✅¡Audio extraído! 🎶")
        except Exception as e:
            await app.send_message(chat_id=message.chat.id, text=f"⭕Error al extraer el audio: {e} ⭕")
        finally:
            if os.path.exists(video_path):
                os.remove(video_path)
            if os.path.exists(audio_path):
                os.remove(audio_path)

    else:
        await app.send_message(chat_id=message.chat.id, text="‼️Responde a un video‼️.")

@app.on_message(filters.command("id"))
async def get_user_id_handler(client, message: Message):
    if await check_security(client, message):
        username = message.text.split(" ")[1]
        user_id = get_user_id(username)
        if user_id is not None:
            await send_success_message(client, message, f"La ID del usuario @{username} es {user_id}")
        else:
            await send_error_message(client, message, f"No se pudo encontrar el usuario @{username}")

@app.on_message(filters.command("about"))
async def about_handler(client, message: Message):
    if await check_security(client, message):
        about_text = "**Acerca del Bot de Compresión de Videos:**\n"
        about_text += "Este bot te permite comprimir videos para reducir su tamaño y facilitar su envío.\n"
        about_text += "**Desarrollador:** [The Big Boss]\n"
        about_text += "**Fecha de Creación:** [2024-11-3]\n"
        about_text += "**Versión:** 3.0\n" # Agrega la versión del bot
        about_text += "**Uso:**\n"
        about_text += "1. Responde al bot con un video.\n"
        about_text += "2. El bot comprimirá el video.\n"
        about_text += "3. Recibirás el video comprimido.\n"
        about_text += "**Comandos:**\n"
        about_text += "/help: Muestra todos los comandos del bot.\n"
        about_text += "/calidad: Ajusta la calidad de compresión.\n"
        about_text += "/convert: Comprime un video.\n"
        about_text += "/descompress: Descomprime un archivo ZIP.\n"
        about_text += "/picarzip: Divide un archivo en partes.\n"
        about_text += "/extract_audio: Extrae el audio de un video.\n"
        about_text += "/id: Obtiene la ID de un usuario.\n"
        await client.send_message(chat_id=message.chat.id, text=about_text)

@app.on_message(filters.command("listuser") & filters.user(admin_list + superadmin_list))
async def list_users_handler(client, message: Message):
    if await check_security(client, message):
        user_list = "Usuarios del bot:\n"
        for user_id in user_list:
            user = await app.get_users(user_id)
            user_list += f"- @{user.username}\n"
        if len(user_list) == "Usuarios del bot:\n":
            user_list = "No hay usuarios en la lista."
        await client.send_message(chat_id=message.chat.id, text=user_list)

@app.on_message(filters.command("listadmin") & filters.user(admin_list + superadmin_list))
async def list_admins_handler(client, message: Message):
    if await check_security(client, message):
        admin_list = "Administradores del bot:\n"
        for user_id in admin_list:
            user = await app.get_users(user_id)
            admin_list += f"- @{user.username}\n"
        if len(admin_list) == "Administradores del bot:\n":
            admin_list = "No hay administradores en la lista."
        await client.send_message(chat_id=message.chat.id, text=admin_list)

@app.on_message(filters.command("listgrup") & filters.user(admin_list + superadmin_list))
async def list_groups_handler(client, message: Message):
    if await check_security(client, message):
        group_list = "Grupos del bot:\n"
        for group_id in group_list:
            group = await app.get_chat(group_id)
            group_list += f"- {group.title} (ID: {group.id})\n"
        if len(group_list) == "Grupos del bot:\n":
            group_list = "No hay grupos en la lista."
        await client.send_message(chat_id=message.chat.id, text=group_list)

@app.on_message(filters.command("banlist") & filters.user(admin_list + superadmin_list))
async def list_banned_users_handler(client, message: Message):
    if await check_security(client, message):
        banned_list = "Usuarios bloqueados del bot:\n"
        for user_id in banned_users:
            user = await app.get_users(user_id)
            banned_list += f"- @{user.username}\n"
        if len(banned_list) == "Usuarios bloqueados del bot:\n":
            banned_list = "No hay usuarios bloqueados en la lista."
        await client.send_message(chat_id=message.chat.id, text=banned_list)

@app.on_message(filters.command("infouser") & filters.user(admin_list + superadmin_list))
async def infouser_handler(client, message: Message):
    if await check_security(client, message):
        try:
            message_text = message.text.split(" ", 1)[1]
            for user_id in user_list:
                await client.send_message(chat_id=user_id, text=f"📢 {message_text}")
            for group_id in group_list:
                await client.send_message(chat_id=group_id, text=f"📢 {message_text}")
            await send_success_message(client, message, "Mensaje enviado a todos los usuarios y grupos.")
        except IndexError:
            await send_error_message(client, message, "Debes proporcionar un mensaje para enviar.")
        except Exception as e:
            await send_error_message(client, message, f"Error al enviar el mensaje: {e}")

@app.on_message(filters.command("soport") & filters.user(user_list + admin_list + superadmin_list))
async def suport_handler(client, message: Message):
    if await check_security(client, message):
        try:
            message_text = message.text.split(" ", 1)[1]
            for superadmin_id in superadmin_list:
                await client.send_message(chat_id=superadmin_id, text=f"📩 Soporte de @{message.from_user.username}: {message_text}")
                await client.pin_message(chat_id=superadmin_id, message_id=message.message_id)
            await send_success_message(client, message, "Mensaje enviado al administrador supremo.")
        except IndexError:
            await send_error_message(client, message, "Debes proporcionar un mensaje para enviar.")
        except Exception as e:
            await send_error_message(client, message, f"Error al enviar el mensaje: {e}")

app.run()
