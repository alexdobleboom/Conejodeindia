import pyrogram
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pyrogram.errors import PeerIdInvalid, UserPrivacyRestrictedError
import os
import subprocess
import time
from typing import Tuple
import hashlib
import datetime

# Credenciales del bot
api_id = 24288670
api_hash = '81c58005802498656d6b689dae1edacc'
bot_token = '7507770865:AAFDQ0Lbuo5Ca-mTnqSa-dK_UJENs5B2v1Q'

# ID del canal del bot
channel_id = -1001759156017 # Reemplaza con el ID de tu canal (https://t.me/AnimalProjets)
# ID del chat del desarrollador
developer_chat_id = -1001836592397 # Reemplaza con el ID de tu chat (t.me/TheDemonsuprem)

# Listas de usuarios y administradores
users = ['@TheFemonsuprem', '@user2']
admins = ['@TheDemonsuprem', '@admin2']
super_admins = ['@TheDemonsuprem']

# Límite de tamaño del video por defecto
max_size = 1024 * 1024 * 1024 # 1 GB
# Calidad por defecto
default_quality = "resolution=640x480 crf=32 audio_bitrate=60k fps=18 preset=ultrafast codec=libx265"

# Crea el cliente de Pyrogram
app = Client('my_bot', api_id, api_hash, bot_token=bot_token)

# Mensaje de inicio
start_message = "🤖 Bot encendido 🚀\n\n¡Bienvenido al Bot de Compresión de Videos!\n\nEnvía un video para que lo comprima."

# Mensaje de acerca del bot
about_message = """
Soy un bot creado por [@Thedemonsuprem] para comprimir videos.

Versión: 3.0
Fecha de creación: [12 de noviembre del 2024]
"""

# Función para validar usuarios
async def validate_user(client, message, user_list):
    try:
        user_id = message.from_user.id
        for user in user_list:
            if user.startswith('@'):
                user = await client.get_users(user)
                if user_id == user.id:
                    return True
        return False
    except (PeerIdInvalid, UserPrivacyRestrictedError):
        return False

# Función para comprimir videos
@app.on_message(filters.video)
async def compress_video(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"

    if not await validate_user(client, message, users):
        await client.send_message(message.chat.id, "❌ No tienes permiso para usar este comando. ❌")
        return

    # Obtiene el video del mensaje
    video_id = message.video.file_id
    file_name = message.video.file_name
    file_size = message.video.file_size
    file_type = message.video.mime_type

    # Valida el tamaño del video
    if file_size > max_size:
        await client.send_message(message.chat.id, f"El tamaño del video es demasiado grande ({file_size / 1024 / 1024:.2f} MB). El límite máximo es {max_size / 1024 / 1024:.2f} MB.")
        return

    # Descarga el video
    download_message = await client.send_message(message.chat.id, "⏳ Descargando video...",
                              reply_markup=InlineKeyboardMarkup(
                                  [[InlineKeyboardButton("Cancelar", callback_data='cancel')]]
                              ))
    original_video_path = await client.download_media(message.video, file_name)
    await download_message.delete()

    # Comprime el video
    convert_message = await client.send_message(message.chat.id, "⚙️ Convirtiendo video...",
                              reply_markup=InlineKeyboardMarkup(
                                  [[InlineKeyboardButton("Cancelar", callback_data='cancel')]]
                              ))
    compressed_file_name = f'{file_name}_compressed.mp4'
    process = subprocess.Popen(
        ['ffmpeg', '-i', original_video_path, '-map', '0', '-c:v', 'libx265', '-preset', 'ultrafast', '-crf', '32',
         '-c:a', 'aac', '-b:a', '60k', '-r', '18', '-vf', 'scale=640:480', compressed_file_name],
        stderr=subprocess.PIPE, text=True
    )

    # Manejo de la cancelación
    cancel_message_id = convert_message.id # Guardamos el ID del mensaje para editarlo
    while True:
        output = process.stderr.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())

        # Actualiza el mensaje de progreso
        await client.edit_message_text(chat_id=message.chat.id, message_id=cancel_message_id, text=output.strip())

    # Verificar si el proceso se canceló
    if process.poll() == 0:
        # Calcula el tamaño del archivo comprimido
        compressed_file_size = os.path.getsize(compressed_file_name)

        # Envía el video comprimido con la descripción
        upload_message = await client.send_message(message.chat.id, "📥Subiendo Videos📤... 0%",
                                  reply_markup=InlineKeyboardMarkup(
                                      [[InlineKeyboardButton("Cancelar", callback_data='cancel')]]
                                  ))

        async def progress_callback(current, total):
            progress = (current * 100) // total
            await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=upload_message.id,
                text=f"📥Subiendo Videos📤... {progress}%"
            )

        await client.send_video(
            chat_id=message.chat.id,
            video=compressed_file_name,
            caption=f"✨ Video comprimido: ✨\n\n"
                    f"Nombre: {file_name}\n"
                    f"Peso original: {file_size / 1024 / 1024:.2f} MB\n"
                    f"Peso comprimido: {compressed_file_size / 1024 / 1024:.2f} MB\n",
            progress=progress_callback
        )

    else:
        await client.send_message(message.chat.id, "🚫 El proceso de compresión fue cancelado. 🚫")

    # Elimina el archivo original
    os.remove(original_video_path)

    # Elimina el archivo comprimido
    os.remove(compressed_file_name)

    except Exception as e:
        await client.send_message(message.chat.id, f"❌ Error al comprimir el video: {e} ❌")

# Función para añadir usuarios
@app.on_message(filters.command(['add']))
async def add_user(client, message):
    try:
        # Validar usuarios
        if not await validate_user(client, message, admins + super_admins):
            await client.send_message(message.chat.id, "No tienes permiso para usar este comando.")
            return

        # Obtener el nombre de usuario
        username = message.text.split()[1]

        # Obtener el usuario
        user = await client.get_users(username)

        # Agregar usuario a la lista
        users.append(username)
        await client.send_message(message.chat.id, f"✅ Usuario {username} agregado exitosamente. ✅")

    except Exception as e:
        await client.send_message(message.chat.id, f"❌ Error al agregar usuario: {e} ❌")

# Función para banear usuarios
@app.on_message(filters.command(['ban']))
async def ban_user(client, message):
    try:
        # Validar usuarios
        if not await validate_user(client, message, admins + super_admins):
            await client.send_message(message.chat.id, "No tienes permiso para usar este comando.")
            return

        # Obtener el nombre de usuario
        username = message.text.split()[1]

        # Obtener el usuario
        user = await client.get_users(username)

        # Eliminar usuario de la lista
        if username in users:
            users.remove(username)
            await client.send_message(message.chat.id, f"✅ Usuario {username} baneado exitosamente. ✅")
        else:
            await client.send_message(message.chat.id, f"❌ El usuario {username} no está en la lista. ❌")

    except Exception as e:
        await client.send_message(message.chat.id, f"❌ Error al banear usuario: {e} ❌")

# Función para añadir administradores
@app.on_message(filters.command(['addadmin']))
async def add_admin(client, message):
    try:
        # Validar usuarios
        if not await validate_user(client, message, admins + super_admins):
            await client.send_message(message.chat.id, "No tienes permiso para usar este comando.")
            return

        # Obtener el nombre de usuario
        username = message.text.split()[1]

        # Obtener el usuario
        user = await client.get_users(username)

        # Agregar administrador a la lista
        admins.append(username)
        await client.send_message(message.chat.id, f"✅ Administrador {username} agregado exitosamente. ✅")

    except Exception as e:
        await client.send_message(message.chat.id, f"❌ Error al agregar administrador: {e} ❌")

# Función para banear administradores
@app.on_message(filters.command(['banadmin']))
async def ban_admin(client, message):
    try:
        # Validar usuarios
        if not await validate_user(client, message, super_admins):
            await client.send_message(message.chat.id, "No tienes permiso para usar este comando.")
            return

        # Obtener el nombre de usuario
        username = message.text.split()[1]

        # Obtener el usuario
        user = await client.get_users(username)

        # Eliminar administrador de la lista
        if username in admins:
            admins.remove(username)
            await client.send_message(message.chat.id, f"✅ Administrador {username} baneado exitosamente. ✅")
        else:
            await client.send_message(message.chat.id, f"❌ El administrador {username} no está en la lista. ❌")

    except Exception as e:
        await client.send_message(message.chat.id, f"❌ Error al banear administrador: {e} ❌")

# Función para enviar información a todos los usuarios
@app.on_message(filters.command(['info']))
async def send_info(client, message):
    try:
        # Validar usuarios
        if not await validate_user(client, message, super_admins):
            await client.send_message(message.chat.id, "No tienes permiso para usar este comando.")
            return

        # Obtener el texto de la información
        info_text = message.text.split()[1:]
        info_text = ' '.join(info_text)

        # Envía la información a todos los usuarios
        for user in users:
            if user.startswith('@'):
                user = await client.get_users(user)
                await client.send_message(user.id, info_text)

        await client.send_message(message.chat.id, "✅ Información enviada a todos los usuarios. ✅")

    except Exception as e:
        await client.send_message(message.chat.id, f"❌ Error al enviar la información: {e} ❌")

# Función para cambiar el límite del tamaño del video
@app.on_message(filters.command(['max']))
async def set_max_size(client, message):
    try:
        # Validar usuarios
        if not await validate_user(client, message, admins + super_admins):
            await client.send_message(message.chat.id, "No tienes permiso para usar este comando.")
            return

        # Obtener el nuevo límite del tamaño
        new_max_size = message.text.split()[1]

        # Convierte el tamaño a bytes
        try:
            if 'Gb' in new_max_size:
                new_max_size = int(new_max_size.replace('Gb', '')) * 1024 * 1024 * 1024
            elif 'Mb' in new_max_size:
                new_max_size = int(new_max_size.replace('Mb', '')) * 1024 * 1024
            elif 'kb' in new_max_size:
                new_max_size = int(new_max_size.replace('kb', '')) * 1024
            else:
                new_max_size = int(new_max_size)
        except ValueError:
            await client.send_message(message.chat.id, "Formato de tamaño inválido. Usa 'Gb', 'Mb', 'kb' o bytes.")
            return

        # Actualiza el límite del tamaño
        global max_size
        max_size = new_max_size
        await client.send_message(message.chat.id, f"✅ Límite del tamaño del video actualizado a {max_size / 1024 / 1024:.2f} MB. ✅")

    except Exception as e:
        await client.send_message(message.chat.id, f"❌ Error al actualizar el límite del tamaño: {e} ❌")

# Función para cambiar la calidad por defecto
@app.on_message(filters.command(['calidad']))
async def set_quality(client, message):
    try:
        # Validar usuarios
        if not await validate_user(client, message, users + admins + super_admins):
            await client.send_message(message.chat.id, "No tienes permiso para usar este comando.")
            return

        # Obtener la nueva calidad
        new_quality = message.text.split()[1]

        # Actualiza la calidad por defecto
        global default_quality
        default_quality = new_quality
        await client.send_message(message.chat.id, f"✅ Calidad por defecto actualizada a: {new_quality} ✅")

    except Exception as e:
        await client.send_message(message.chat.id, f"❌ Error al actualizar la calidad por defecto: {e} ❌")

# Función para mostrar la lista de usuarios
@app.on_message(filters.command(['listuser']))
async def list_users(client, message):
    try:
        # Validar usuarios
        if not await validate_user(client, message, admins + super_admins):
            await client.send_message(message.chat.id, "No tienes permiso para usar este comando.")
            return

        # Muestra la lista de usuarios
        if users:
            await client.send_message(message.chat.id, f"Lista de usuarios:\n{', '.join(users)}")
        else:
            await client.send_message(message.chat.id, "No hay usuarios en la lista.")

    except Exception as e:
        await client.send_message(message.chat.id, f"❌ Error al mostrar la lista de usuarios: {e} ❌")

# Función para mostrar la lista de administradores
@app.on_message(filters.command(['listadmin']))
async def list_admins(client, message):
    try:
        # Validar usuarios
        if not await validate_user(client, message, super_admins):
            await client.send_message(message.chat.id, "No tienes permiso para usar este comando.")
            return

        # Muestra la lista de administradores
        if admins:
            await client.send_message(message.chat.id, f"Lista de administradores:\n{', '.join(admins)}")
        else:
            await client.send_message(message.chat.id, "No hay administradores en la lista.")

    except Exception as e:
        await client.send_message(message.chat.id, f"❌ Error al mostrar la lista de administradores: {e} ❌")

# Función para manejar el comando /start
@app.on_message(filters.command(['start']))
async def start(client, message):
    await message.reply(start_message,
                       reply_markup=InlineKeyboardMarkup(
                           [[InlineKeyboardButton("Chat del Desarrollador", url=f"https://t.me/{developer_chat_id}"),
                             InlineKeyboardButton("Canal del Bot", url=f"https://t.me/{channel_id}")]]
                       )
    )

# Función para manejar el comando /help
@app.on_message(filters.command(['help']))
async def help(client, message):
    await client.send_message(
        message.chat.id,
        "**Comandos disponibles:**\n\n"
        f"**/start** - Inicia el bot.\n"
        f"**/help** - Muestra la lista de comandos y su funcionamiento.\n"
        f"**/add** - Añadir un usuario a la lista de usuarios. Solo para administradores o administradores supremos. Escribe este comando seguido del nombre de usuario (@nombredeusuario).\n"
        f"**/ban** - Banear un usuario. Solo para administradores o administradores supremos. Escribe este comando seguido del nombre de usuario (@nombredeusuario).\n"
        f"**/addadmin** - Añadir un administrador a la lista de administradores. Solo para administradores o administradores supremos. Escribe este comando seguido del nombre de usuario (@nombredeusuario).\n"
        f"**/banadmin** - Banear un administrador. Solo para administradores supremos. Escribe este comando seguido del nombre de usuario (@nombredeusuario).\n"
        f"**/info** - Permite que los administradores supremos envíen información a todos los usuarios del Bot. Escribe este comando seguido del texto de la información.\n"
        f"**/about** - Muestra información del Bot.\n"
        f"**/max** - Aumenta o disminuye el límite del peso de los videos que el Bot puede soportar. Solo para administradores o administradores supremos. Escribe este comando seguido del nuevo límite (por ejemplo, /max 1Gb o /max 3Mb).\n"
        f"**/calidad** - Permite cambiar la calidad por defecto con la que el Bot convierte. Escribe este comando seguido de los parámetros de calidad (por ejemplo, /calidad resolution=640x480 crf=32 audio_bitrate=60k fps=18 preset=veryfast codec=libx264).\n"
        f"**/listuser** - Permite ver la lista de usuarios del Bot. Solo para administradores o administradores supremos.\n"
        f"**/listadmin** - Permite ver la lista de administradores del Bot. Solo para administradores supremos.\n"
    )

# Función para manejar el comando /about
@app.on_message(filters.command(['about']))
async def about(client, message):
    await message.reply(about_message)

# Función para manejar la cancelación de la compresión
@app.on_callback_query()
async def callback_query_handler(client, query):
    if query.data == 'cancel':
        await client.send_message(query.message.chat.id, "Proceso de compresión cancelado.")
        await query.message.delete()

# Función para fijar mensajes en la parte superior del chat
async def pin_message(client, chat_id, message_id):
    try:
        await client.pin_chat_message(chat_id, message_id, disable_notification=True)
    except Exception as e:
        print(f"Error al fijar el mensaje: {e}")

# Función para notificar a los administradores
async def notify_admins(client, message, error_message):
    try:
        for admin in admins + super_admins:
            if admin.startswith('@'):
                admin = await client.get_users(admin)
                await client.send_message(admin.id, f"Error en el bot: {error_message}\n\nMensaje del usuario: {message.text}")
    except Exception as e:
        print(f"Error al notificar a los administradores: {e}")

# Función para manejar errores
@app.on_exception()
async def error_handler(client, exception, message):
    try:
        # Obtener el error
        error_message = f"{exception.__class__.__name__}: {str(exception)}"

        # Notificar a los administradores
        await notify_admins(client, message, error_message)

        # Enviar un mensaje al usuario
        await client.send_message(
            message.chat.id,
            f"Ha ocurrido un error. Por favor, contacta al administrador.\n\nError: {error_message}"
        )
    except Exception as e:
        print(f"Error al manejar la excepción: {e}")

# Ejecutar el bot
app.run()
