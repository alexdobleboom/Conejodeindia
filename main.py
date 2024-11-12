import pyrogram
import asyncio
import os
import re
import time

# Configuraciones del bot
BOT_TOKEN = "7507770865:AAFDQ0Lbuo5Ca-mTnqSa-dK_UJENs5B2v1Q"
API_ID = 24288670 # Reemplaza con tu API ID de Telegram
API_HASH = "81c58005802498656d6b689dae1edacc" # Reemplaza con tu API hash de Telegram
ADMIN_ID = 7551486576 # Reemplaza con tu ID de usuario de Telegram
MAX_VIDEO_SIZE = 1024 * 1024 * 1024 # 1GB por defecto

# Calidad de conversión por defecto
DEFAULT_QUALITY = "resolution=640x480 crf=32 audio_bitrate=60k fps=18 preset=ultrafast codec=libx265"

# Diccionarios para almacenar usuarios, administradores y administradores supremos
users = {}
admins = {}
super_admins = {ADMIN_ID: True}

# Función para convertir un video
async def convertir_video(client, message, quality):
    file_id = message.video.file_id
    file_size = message.video.file_size
    file_name = message.video.file_name
    chat_id = message.chat.id
    start_time = time.time()

    # Verificar el tamaño del archivo
    if file_size > MAX_VIDEO_SIZE:
        await client.send_message(
            chat_id=chat_id,
            text="El video es demasiado grande. El tamaño máximo permitido es de {}.\n\n¡Intenta con un video más pequeño!".format(
                human_readable_size(MAX_VIDEO_SIZE)
            ),
        )
        return

    # Obtener la extensión del archivo
    file_extension = os.path.splitext(file_name)[1]

    # Obtener el nombre del archivo
    file_name = f"{message.video.file_unique_id}{file_extension}"

    # Descargando el video
    await client.send_message(
        chat_id=chat_id,
        text="⏳ Descargando el video... 📥",
    )
    await client.download_media(
        message=message, file_name=file_name, progress=None,
    )

    # Convirtiendo el video
    await client.send_message(
        chat_id=chat_id,
        text="🎬 Convirtiendo el video... ⚙️",
    )
    command = f'ffmpeg -i "{file_name}" -map 0 -c:v libx265 -preset ultrafast -crf 23 -c:a copy -b:a 60k -f mp4 "{file_name}.mp4"'
    os.system(command)

    # Subiendo el video
    await client.send_message(
        chat_id=chat_id,
        text="⬆️ Subiendo el video... 🚀",
    )

    # Calcular el tiempo de procesamiento
    end_time = time.time()
    processing_time = end_time - start_time
    processing_time_str = time.strftime("%H:%M:%S", time.gmtime(processing_time))

    # Obtener la duración del video
    duration = message.video.duration
    duration_str = time.strftime("%H:%M:%S", time.gmtime(duration))

    # Obtener el tamaño del video original y convertido
    original_size = human_readable_size(file_size)
    converted_size = human_readable_size(os.path.getsize(f"{file_name}.mp4"))

    # Enviar el video convertido
    await client.send_video(
        chat_id=chat_id,
        video=f"{file_name}.mp4",
        caption=f"""
        ꧁༺ 𝑭𝒊𝒏𝒂𝒍𝒊𝒛𝒂𝒅𝒐 ༻꧂
        ✮𝑵𝒐𝒎𝒃𝒓𝒆 𝒅𝒆𝒍 𝒗𝒊𝒅𝒆𝒐: {file_name}
        ×‌×𝑷𝒆𝒔𝒐 𝑶𝒓𝒊𝒈𝒊𝒏𝒂𝒍: {original_size}
        ×‌×𝑷𝒆𝒔𝒐 𝑷𝒓𝒐𝒄𝒆𝒔𝒂𝒅𝒐: {converted_size}
        𖤍𝑻𝒊𝒆𝒎𝒑𝒐 𝒅𝒆 𝑷𝒓𝒐𝒄𝒆𝒔𝒂𝒎𝒊𝒆𝒏𝒕𝒐: {processing_time_str}
        ✧𝑻𝒊𝒆𝒎𝒑𝒐 𝒅𝒆𝒍 𝑽𝒊𝒅𝒆𝒐: {duration_str}
        ♣¡𝑸𝒖𝒆 𝒍𝒐 𝒅𝒊𝒔𝒇𝒓𝒖𝒕𝒆𝒔
        """,
        progress=None,
    )

    # Eliminar los archivos temporales
    os.remove(file_name)
    os.remove(f"{file_name}.mp4")

# Función para verificar permisos de administrador
async def check_admin(client, message, user_id):
    chat_member = await client.get_chat_member(
        chat_id=message.chat.id, user_id=user_id,
    )
    if chat_member.status == "administrator" or chat_member.status == "creator":
        return True
    return False

# Función para verificar permisos de usuario
async def check_user(client, message, user_id):
    if user_id in users:
        return True
    return False

# Función para enviar una alerta al administrador supremo
async def send_alert(client, message, reason):
    await client.send_message(
        chat_id=ADMIN_ID, text=f"🚨 Alerta! {reason} ({message.from_user.username})"
    )

# Función para convertir bytes a una cadena legible por humanos
def human_readable_size(size):
    if size < 1024:
        return f"{size} B"
    elif size < 1048576:
        return f"{size // 1024} KB"
    elif size < 1073741824:
        return f"{size // 1048576} MB"
    else:
        return f"{size // 1073741824} GB"

# Handler para el comando /start
@pyrogram.Client.on_message(pyrogram.filters.command(["start"]))
async def start_handler(client, message):
    user_id = message.from_user.id

    # Verificar si el usuario es un usuario del bot
    if not check_user(client, message, user_id):
        await send_alert(client, message, "Usuario no autorizado")
        return

    await client.send_message(
        chat_id=message.chat.id,
        text="¡Hola! 👋 Bienvenido al Bot de Conversión de Vídeo 🎥. Usa /help para ver los comandos disponibles.",
    )

# Handler para el comando /help
@pyrogram.Client.on_message(pyrogram.filters.command(["help"]))
async def help_handler(client, message):
    user_id = message.from_user.id

    # Verificar si el usuario es un usuario del bot
    if not check_user(client, message, user_id):
        await send_alert(client, message, "Usuario no autorizado")
        return

    await client.send_message(
        chat_id=message.chat.id,
        text="""
        ✨ **Comandos disponibles:** ✨

        * `/start` - Inicia el Bot 
        * `/help` - Muestra la lista de comandos, como funciona el Bot y como funcionan los comandos.
        * `/add` - Añade un usuario al Bot atraves de su @usuario (solo admin o admin supremos)
        * `/ban` - Banea un usuario del Bot atraves de su @usuario (solo admin o admin supremos)
        * `/addadmin` - le da permisos de admin a un usuario atraves de su @usuario (solo admin o admin supremos)
        * `/banadmin` - banea un administrador atraves de su @usuario (solo admin o administrador supremos)
        * `/info` - permite que los administradores le den una información a todos los usuarios del Bot&nbsp; (solo admin supremo)
        * `/about` - Muestra información del Bot ejemplo (fecha de creación, hora de crecion, desarrollar, version.) (todos los usuarios del Bot)
        * `/max` - aumenta o disminuye el límite del peso de los videos que el Bot puede soportar ejemplo (/max 1Gb o /max 3Mb) solo admin o admin supremos
        * `/calidad` - permite que todos los usuarios puedan cambiar la calidad por defecto con la que el Bot convierte ejemplo (/calidad resolution=640x480 crf=32 audio_bitrate=60k fps=18 preset=veryfast codec=libx264) todos los usuarios del Bot.
        * `/listuser` - permite ver la lista de usuario del Bot (solo admin o usuarios supremos)
        * `/listadmin` - permite ver la lista de admin del Bot (solo admin supremos)

        **Ejemplos de uso de los comandos:**

        * `/add @Sasuke286` 
        * `/ban @Sasuke286` 
        * `/addadmin @Juan`
        * `/banadmin @Juan` 
        * `/max 5Mb`
        * `/calidad resolution=640x480 crf=32 audio_bitrate=60k fps=18 preset=veryfast codec=libx264` 
        """,
    )

# Handler para el comando /add (agregar usuario)
@pyrogram.Client.on_message(pyrogram.filters.command(["add"]))
async def add_handler(client, message):
    user_id = message.from_user.id

    # Verificar si el usuario es administrador
    if not (check_admin(client, message, user_id) or super_admins.get(user_id)):
        await send_alert(client, message, "Comando restringido")
        return

    # Obtener el usuario a agregar
    match = re.search(r"@(\w+)", message.text)
    if match:
        username = match.group(1)
        try:
            user_data = await client.get_users(username)
            users[user_data.id] = True
            await client.send_message(
                chat_id=message.chat.id,
                text=f"✅ Usuario @{username} agregado correctamente al Bot 🤖.",
            )
        except Exception as e:
            await client.send_message(
                chat_id=message.chat.id,
                text=f"❌ Error al agregar usuario: {e}",
            )
    else:
        await client.send_message(
            chat_id=message.chat.id,
            text="Uso incorrecto del comando. Ejemplo: /add @usuario",
        )

# Handler para el comando /ban (banear usuario)
@pyrogram.Client.on_message(pyrogram.filters.command(["ban"]))
async def ban_handler(client, message):
    user_id = message.from_user.id

    # Verificar si el usuario es administrador
    if not (check_admin(client, message, user_id) or super_admins.get(user_id)):
        await send_alert(client, message, "Comando restringido")
        return

    # Obtener el usuario a banear
    match = re.search(r"@(\w+)", message.text)
    if match:
        username = match.group(1)
        try:
            user_data = await client.get_users(username)
            if user_data.id in users:
                del users[user_data.id]
                await client.send_message(
                    chat_id=message.chat.id,
                    text=f"🚫 Usuario @{username} baneado correctamente del Bot 🤖.",
                )
            else:
                await client.send_message(
                    chat_id=message.chat.id,
                    text=f"🤔 Usuario @{username} no está en la lista de usuarios del Bot 🤖.",
                )
        except Exception as e:
            await client.send_message(
                chat_id=message.chat.id,
                text=f"❌ Error al banear usuario: {e}",
            )
    else:
        await client.send_message(
            chat_id=message.chat.id,
            text="Uso incorrecto del comando. Ejemplo: /ban @usuario",
        )

# Handler para el comando /addadmin (agregar administrador)
@pyrogram.Client.on_message(pyrogram.filters.command(["addadmin"]))
async def addadmin_handler(client, message):
    user_id = message.from_user.id

    # Verificar si el usuario es administrador supremo
    if not super_admins.get(user_id):
        await send_alert(client, message, "Comando restringido")
        return

    # Obtener el usuario a agregar como administrador
    match = re.search(r"@(\w+)", message.text)
    if match:
        username = match.group(1)
        try:
            user_data = await client.get_users(username)
            admins[user_data.id] = True
            await client.send_message(
                chat_id=message.chat.id,
                text=f"👮‍♂️ Usuario @{username} agregado como administrador del Bot 🤖 correctamente.",
            )
        except Exception as e:
            await client.send_message(
                chat_id=message.chat.id,
                text=f"❌ Error al agregar administrador: {e}",
            )
    else:
        await client.send_message(
            chat_id=message.chat.id,
            text="Uso incorrecto del comando. Ejemplo: /addadmin @usuario",
        )

# Handler para el comando /banadmin (banear administrador)
@pyrogram.Client.on_message(pyrogram.filters.command(["banadmin"]))
async def banadmin_handler(client, message):
    user_id = message.from_user.id

    # Verificar si el usuario es administrador supremo
    if not super_admins.get(user_id):
        await send_alert(client, message, "Comando restringido")
        return

    # Obtener el administrador a banear
    match = re.search(r"@(\w+)", message.text)
    if match:
        username = match.group(1)
        try:
            user_data = await client.get_users(username)
            if user_data.id in admins:
                del admins[user_data.id]
                await client.send_message(
                    chat_id=message.chat.id,
                    text=f"👮‍♂️ Administrador @{username} baneado correctamente del Bot 🤖.",
                )
            else:
                await client.send_message(
                    chat_id=message.chat.id,
                    text=f"🤔 Administrador @{username} no está en la lista de administradores del Bot 🤖.",
                )
        except Exception as e:
            await client.send_message(
                chat_id=message.chat.id,
                text=f"❌ Error al banear administrador: {e}",
            )
    else:
        await client.send_message(
            chat_id=message.chat.id,
            text="Uso incorrecto del comando. Ejemplo: /banadmin @usuario",
        )

# Handler para el comando /info (enviar información a todos los usuarios)
@pyrogram.Client.on_message(pyrogram.filters.command(["info"]))
async def info_handler(client, message):
    user_id = message.from_user.id

    # Verificar si el usuario es administrador supremo
    if not super_admins.get(user_id):
        await send_alert(client, message, "Comando restringido")
        return

    # Obtener el mensaje de información
    info_message = message.text.split(" ", 1)[1]

    # Enviar el mensaje a todos los usuarios
    for user_id in users:
        try:
            await client.send_message(chat_id=user_id, text=info_message)
        except Exception as e:
            print(f"Error al enviar mensaje a usuario {user_id}: {e}")

    await client.send_message(
        chat_id=message.chat.id,
        text=f"✅ Mensaje enviado a todos los usuarios correctamente del Bot 🤖.",
    )

# Handler para el comando /about (mostrar información del bot)
@pyrogram.Client.on_message(pyrogram.filters.command(["about"]))
async def about_handler(client, message):
    user_id = message.from_user.id

    # Verificar si el usuario es un usuario del bot
    if not check_user(client, message, user_id):
        await send_alert(client, message, "Usuario no autorizado")
        return

    await client.send_message(
        chat_id=message.chat.id,
        text="""
        🤖 **Bot de Conversión de Vídeo** 🎥

        * **Fecha de creación:** 2023-10-26
        * **Hora de creación:** 12:00 AM
        * **Desarrollador:** @TuNombreDeUsuario
        * **Versión:** 1.0
        """,
    )

# Handler para el comando /max (cambiar tamaño máximo del video)
@pyrogram.Client.on_message(pyrogram.filters.command(["max"]))
async def max_handler(client, message):
    user_id = message.from_user.id

    # Verificar si el usuario es administrador
    if not (check_admin(client, message, user_id) or super_admins.get(user_id)):
        await send_alert(client, message, "Comando restringido")
        return

    # Obtener el nuevo tamaño máximo
    match = re.search(r"(\d+)\s*([a-zA-Z]+)", message.text)
    if match:
        size_value = int(match.group(1))
        size_unit = match.group(2).lower()
        if size_unit == "kb":
            new_size = size_value * 1024
        elif size_unit == "mb":
            new_size = size_value * 1024 * 1024
        elif size_unit == "gb":
            new_size = size_value * 1024 * 1024 * 1024
        else:
            await client.send_message(
                chat_id=message.chat.id,
                text="Unidad de tamaño inválida. Usa KB, MB o GB.",
            )
            return

        global MAX_VIDEO_SIZE
        MAX_VIDEO_SIZE = new_size
        await client.send_message(
            chat_id=message.chat.id,
            text=f"✅ Tamaño máximo de video cambiado a {human_readable_size(new_size)}.",
        )
    else:
        await client.send_message(
            chat_id=message.chat.id,
            text="Uso incorrecto del comando. Ejemplo: /max 5MB",
        )

# Handler para el comando /calidad (cambiar calidad de conversión)
@pyrogram.Client.on_message(pyrogram.filters.command(["calidad"]))
async def calidad_handler(client, message):
    user_id = message.from_user.id

    # Verificar si el usuario es un usuario del bot
    if not check_user(client, message, user_id):
        await send_alert(client, message, "Usuario no autorizado")
        return

    # Obtener la nueva calidad
    new_quality = message.text.split(" ", 1)[1]
    global DEFAULT_QUALITY
    DEFAULT_QUALITY = new_quality
    await client.send_message(
        chat_id=message.chat.id,
        text=f"✅ Calidad de conversión cambiada a: {new_quality}",
    )

# Handler para el comando /listuser (mostrar lista de usuarios)
@pyrogram.Client.on_message(pyrogram.filters.command(["listuser"]))
async def listuser_handler(client, message):
    user_id = message.from_user.id

    # Verificar si el usuario es administrador
    if not (check_admin(client, message, user_id) or super_admins.get(user_id)):
        await send_alert(client, message, "Comando restringido")
        return

    if users:
        user_list = "\n".join(f"@{user_data.username}" for user_id, user_data in users.items())
        await client.send_message(
            chat_id=message.chat.id, text=f"Lista de usuarios:\n{user_list}"
        )
    else:
        await client.send_message(
            chat_id=message.chat.id, text="No hay usuarios en la lista."
        )

# Handler para el comando /listadmin (mostrar lista de administradores)
@pyrogram.Client.on_message(pyrogram.filters.command(["listadmin"]))
async def listadmin_handler(client, message):
    user_id = message.from_user.id

    # Verificar si el usuario es administrador supremo
    if not super_admins.get(user_id):
        await send_alert(client, message, "Comando restringido")
        return

    if admins:
        admin_list = "\n".join(
            f"@{user_data.username}" for user_id, user_data in admins.items()
        )
        await client.send_message(
            chat_id=message.chat.id, text=f"Lista de administradores:\n{admin_list}"
        )
    else:
        await client.send_message(
            chat_id=message.chat.id, text="No hay administradores en la lista."
        )

# Handler para videos en grupos
@pyrogram.Client.on_message(pyrogram.filters.video & ~pyrogram.filters.private)
async def video_handler(client, message):
    user_id = message.from_user.id

    # Verificar si el usuario es un usuario del bot
    if not check_user(client, message, user_id):
        await send_alert(client, message, "Usuario no autorizado")
        return

    await convertir_video(client, message, DEFAULT_QUALITY)

# Crear la instancia del cliente de Pyrogram
app = pyrogram.Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Ejecutar el bot
async def main():
    await app.start()
    print("Bot iniciado.")
    await app.idle()

asyncio.run(main())
