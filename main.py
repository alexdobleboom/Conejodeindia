import os
import subprocess
import datetime
import pyrogram
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, RPCError

# Datos de la API (reemplaza con tus propios datos)
api_id = 24288670 # Reemplaza con tu API ID
api_hash = "81c58005802498656d6b689dae1edacc" # Reemplaza con tu API Hash
token = "7507770865:AAFDQ0Lbuo5Ca-mTnqSa-dK_UJENs5B2v1Q" # Reemplaza con tu Token de Bot

# Lista de usuarios administrador (reemplaza con los usernames de Telegram)
admin_users = ["@TheDemonsuprem", "@Unadmin2"] # Reemplaza con los usernames de tus administradores

# Límite de tamaño de video (1 GB)
max_video_size = 1024 * 1024 * 1024

# Límite de tamaño de carpeta (2 GB)
max_folder_size = 2 * 1024 * 1024 * 1024

# Configuración de calidad predeterminada
default_quality_settings = [
    "-s",
    "740x480",
    "-crf",
    "28",
    "-b:a",
    "65k",
    "-fps",
    "24",
    "-preset",
    "veryfast",
    "-c:v",
    "libx264",
]

# Lista de usuarios baneados (inicialmente vacía)
banned_users = []

# Crea el cliente de Telegram
app = Client("my_bot", api_id, api_hash, bot_token=token)


# Función para verificar si el usuario está autorizado
async def is_user_authorized(user_id):
    user = await app.get_users(user_id)
    username = user.username
    return username in admin_users


# Función para crear una carpeta para el usuario
def create_user_folder(user_id):
    folder_path = f"./users/{user_id}"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    return folder_path


# Función para calcular el tamaño de una carpeta
def get_folder_size(folder_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size


# Función para comprimir video
async def compress_video(client, message: Message, quality_settings=None):
    username = message.from_user.username or f"user_{message.from_user.id}"
    user_id = message.from_user.id

    # Verificar si el usuario está baneado
    if user_id in banned_users:
        await client.send_message(
            chat_id=message.chat.id, text="🚫 ¡Estás baneado del bot! 🚫"
        )
        return

    # Verificar si el usuario está dentro del límite de almacenamiento
    folder_path = create_user_folder(user_id)
    folder_size = get_folder_size(folder_path)
    if folder_size > max_folder_size:
        await client.send_message(
            chat_id=message.chat.id,
            text="🚫 ¡Has excedido el límite de almacenamiento de tu carpeta (2 GB)! No puedes comprimir más videos. 🚫",
        )
        return

    if message.reply_to_message and message.reply_to_message.video:
        try:
            original_video_path = await client.download_media(
                message.reply_to_message.video, file_name=f"./users/{user_id}/original_video.mp4"
            )
        except Exception as e:
            await client.send_message(
                chat_id=message.chat.id, text=f"🚫 ¡Error al descargar el video! {e} 🚫"
            )
            return

        original_size = os.path.getsize(original_video_path)

        if original_size > max_video_size:
            await client.send_message(
                chat_id=message.chat.id,
                text="🚫 ¡El video excede el límite de tamaño permitido (1 GB)! 🚫",
            )
            return

        await client.send_message(
            chat_id=message.chat.id, text="🔄 ¡Comprimiendo el video! 🔄"
        )

        compressed_video_path = f"{os.path.splitext(original_video_path)[0]}_compressed.mkv"

        # Gestión avanzada para videos pesados (usar opciones de calidad optimizadas)
        if original_size > (max_video_size // 2): # Si el video es mayor a la mitad del límite
            ffmpeg_command = [
                "ffmpeg",
                "-y",
                "-i",
                original_video_path,
                "-preset",
                "ultrafast", # Priorizar velocidad
                "-c:v",
                "libx265", # Usar libx265 para mejor compresión
                "-b:v",
                "1M", # Bitrate de video limitado a 1Mbits/s
                "-b:a",
                "128k", # Bitrate de audio limitado a 128kbits/s
                compressed_video_path,
            ]
        else:
            # Usar la configuración predeterminada o la configuración personalizada
            ffmpeg_command = [
                "ffmpeg",
                "-y",
                "-i",
                original_video_path,
                "-preset",
                "veryfast",
                "-c:v",
                "libx264",
                compressed_video_path,
            ]
            if quality_settings:
                ffmpeg_command.extend(quality_settings)
            else:
                ffmpeg_command.extend(default_quality_settings)

        try:
            start_time = datetime.datetime.now()
            process = subprocess.Popen(
                ffmpeg_command, stderr=subprocess.PIPE, text=True
            )

            while True:
                output = process.stderr.readline()
                if output == "" and process.poll() is not None:
                    break
                if output:
                    print(output.strip())

            # Recuperar tamaño y duración
            compressed_size = os.path.getsize(compressed_video_path)
            duration = subprocess.check_output(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    compressed_video_path,
                ]
            )
            duration = float(duration.strip())
            duration_str = str(datetime.timedelta(seconds=duration))

            processing_time = datetime.datetime.now() - start_time
            processing_time_str = str(processing_time).split(".")[0] # Formato sin microsegundos

            # Descripción para el video comprimido
            description = (
                f"🎉 ¡Proceso Finalizado! 🎉\n"
                f"⏬ Tamaño Original: {original_size // (1024 * 1024)} MB\n"
                f"⏫ Tamaño Comprimido: {compressed_size // (1024 * 1024)} MB\n"
                f"⏱️ Tiempo de Compresión: {processing_time_str}\n"
                f"🎥 Duración del Video: {duration_str}\n"
            )

            # Enviar el video comprimido con la descripción
            await client.send_document(
                chat_id=message.chat.id,
                document=compressed_video_path,
                caption=description,
            )

        except Exception as e:
            await client.send_message(
                chat_id=message.chat.id, text=f"❌ ¡Error al comprimir el video! {e} ❌"
            )
        finally:
            if os.path.exists(original_video_path):
                os.remove(original_video_path)
            if os.path.exists(compressed_video_path):
                os.remove(compressed_video_path)
    else:
        await client.send_message(
            chat_id=message.chat.id, text="🤔 ¡Responde a un video para comprimirlo! 🤔"
        )


# Comando /start
@app.on_message(filters.command("start"))
async def start_handler(client, message: Message):
    await client.send_message(
        chat_id=message.chat.id, text="🤖 ¡Hola! 👋 ¿Qué quieres hacer? 🤔"
    )


# Comando /help
@app.on_message(filters.command("help"))
async def help_handler(client, message: Message):
    help_text = (
        "🤖 Comandos disponibles: 🤖\n\n"
        "/compress - Comprime un video con la calidad predeterminada. Responde a un video para comprimirlo.\n"
        "/calidad - Define la calidad de compresión personalizada. Usa el formato: /calidad resolution=640x480 crf=32 audio_bitrate=60k fps=18 preset=veryfast codec=libx264\n"
        "/mils - Muestra el estado de tu carpeta, incluyendo espacio usado y cantidad de videos.\n"
        "/start - Inicia la interacción con el bot.\n"
        "/help - Muestra esta ayuda.\n\n"
        "👮‍♀️ Comandos de administrador: 👮‍♀️\n\n"
        "/banlist - Muestra la lista de usuarios baneados.\n"
        "/unban - Desbloquea un usuario de la lista de baneados. Usa el formato: /unban [ID de usuario]\n"
        "/broadcast - Envía un mensaje a todos los usuarios. Usa el formato: /broadcast [Mensaje]\n"
        "/about - Muestra información sobre el bot.\n"
        "/calidad_default - Cambia la configuración de calidad predeterminada para la compresión de videos. Usa el formato: /calidad_default resolution=640x480 crf=28 audio_bitrate=65k fps=24 preset=veryfast codec=libx264\n"
        "/max - Cambia el límite de tamaño de video o carpeta. Usa el formato: /max [Tamaño] [video/carpeta]. Ej: /max 5Gb video o /max 2Gb carpeta\n"
        "/stats - Muestra estadísticas generales del bot.\n"
        "/clear_user - Elimina la carpeta de un usuario específico. Usa el formato: /clear_user [ID de usuario]\n"
        "/clear_all - Elimina las carpetas de todos los usuarios."
    )
    await client.send_message(chat_id=message.chat.id, text=help_text)


# Comando /compress
@app.on_message(filters.command("compress"))
async def compress_handler(client, message: Message):
    await compress_video(client, message)


# Comando /calidad
@app.on_message(filters.command("calidad"))
async def quality_handler(client, message: Message):
    quality_settings = message.text.split()[1:]
    if quality_settings:
        await compress_video(client, message, quality_settings=quality_settings)
    else:
        await client.send_message(
            chat_id=message.chat.id,
            text="🤔 Formato de comando incorrecto! 🤔\nUsa: /calidad resolution=640x480 crf=32 audio_bitrate=60k fps=18 preset=veryfast codec=libx264",
        )


# Comando /ls
@app.on_message(filters.command("ls"))
async def ls_handler(client, message: Message):
    user_folder = create_user_folder(message.from_user.id)
    files = os.listdir(user_folder)

    user_info = await app.get_users(message.from_user.id)
    response = f"📁 Carpeta de {user_info.first_name}:\n"
    response += f"🎬 Videos: {len(files)}\n"

    # Calcular días en el bot
    join_date = user_info.joined_date
    if join_date:
        days_in_bot = (datetime.datetime.now() - join_date).days
        response += f"📅 Días en el Bot: {days_in_bot}"

    await client.send_message(chat_id=message.chat.id, text=response)


# Comando /mils
@app.on_message(filters.command("mils"))
async def mils_handler(client, message: Message):
    user_id = message.from_user.id
    folder_path = create_user_folder(user_id)
    folder_size = get_folder_size(folder_path)
    files = os.listdir(folder_path)

    user_info = await app.get_users(message.from_user.id)

    response = f"📁 Carpeta de {user_info.first_name}:\n"
    response += f"💾 Espacio usado: {folder_size // (1024 * 1024)} de 2Gb\n"
    response += f"🎬 Videos: {len(files)}\n"

    # Calcular días en el bot
    join_date = user_info.joined_date
    if join_date:
        days_in_bot = (datetime.datetime.now() - join_date).days
        response += f"📅 Días en el Bot: {days_in_bot}"

    await client.send_message(chat_id=message.chat.id, text=response)


# Comando /max (para administradores)
@app.on_message(filters.command("max") & filters.user(admins))
async def max_handler(client, message: Message):
    global max_video_size, max_folder_size
    try:
        new_max_size_str = message.text.split()[1]
        new_max_size = int(new_max_size_str[:-1])

        if new_max_size_str[-1] == "G":
            new_max_size *= 1024 * 1024 * 1024
        elif new_max_size_str[-1] == "M":
            new_max_size *= 1024 * 1024
        elif new_max_size_str[-1] == "K":
            new_max_size *= 1024

        # Determinar si el comando se aplica al límite de video o carpeta
        if len(message.text.split()) > 2 and message.text.split()[2] == "video":
            max_video_size = new_max_size
            await client.send_message(
                chat_id=message.chat.id,
                text=f"✅ Límite de tamaño de video actualizado a {new_max_size_str}! ✅",
            )
        elif len(message.text.split()) > 2 and message.text.split()[2] == "carpeta":
            max_folder_size = new_max_size
            await client.send_message(
                chat_id=message.chat.id,
                text=f"✅ Límite de tamaño de carpeta actualizado a {new_max_size_str}! ✅",
            )
        else:
            await client.send_message(
                chat_id=message.chat.id,
                text="🤔 Formato de comando incorrecto! 🤔\nUsa: /max [Tamaño] [video/carpeta]\nEjemplo: /max 5Gb video o /max 2Gb carpeta",
            )
    except Exception as e:
        await client.send_message(
            chat_id=message.chat.id,
            text="🤔 Formato de comando incorrecto! 🤔\nUsa: /max [Tamaño] [video/carpeta]\nEjemplo: /max 5Gb video o /max 2Gb carpeta",
        )


# Comando /calidad_default (para administradores)
@app.on_message(filters.command("calidad_default") & filters.user(admins))
async def quality_default_handler(client, message: Message):
    global default_quality_settings
    try:
        new_quality_settings = message.text.split()[1:]
        default_quality_settings = new_quality_settings
        await client.send_message(
            chat_id=message.chat.id,
            text=f"✅ Calidad predeterminada actualizada a: {new_quality_settings}! ✅",
        )
    except Exception as e:
        await client.send_message(
            chat_id=message.chat.id,
            text="🤔 Formato de comando incorrecto! 🤔\nUsa: /calidad_default resolution=640x480 crf=28 audio_bitrate=65k fps=24 preset=veryfast codec=libx264",
        )


# Comando /stats (para administradores)
@app.on_message(filters.command("stats") & filters.user(admins))
async def stats_handler(client, message: Message):
    total_compressed_videos = 0
    total_compressed_size = 0
    for user_id in os.listdir("./users"):
        user_folder = create_user_folder(user_id)
        total_compressed_videos += len(os.listdir(user_folder))
        total_compressed_size += get_folder_size(user_folder)

    stats_message = (
        f"📊 Estadísticas del Bot 📊\n"
        f"✅ Videos Comprimidos: {total_compressed_videos}\n"
        f"💾 Espacio Total Comprimido: {total_compressed_size // (1024 * 1024)} MB"
    )
    await client.send_message(chat_id=message.chat.id, text=stats_message)


# Comando /banlist (para administradores)
@app.on_message(filters.command("banlist") & filters.user(admins))
async def banlist_handler(client, message: Message):
    if banned_users:
        banned_users_str = "\n".join(banned_users)
        await client.send_message(
            chat_id=message.chat.id,
            text=f"🚫 Lista de usuarios baneados: \n{banned_users_str} 🚫",
        )
    else:
        await client.send_message(
            chat_id=message.chat.id, text="🚫 No hay usuarios baneados. 🚫"
        )


# Comando /unban (para administradores)
@app.on_message(filters.command("unban") & filters.user(admins))
async def unban_handler(client, message: Message):
    try:
        user_to_unban = message.text.split()[1]
        if user_to_unban in banned_users:
            banned_users.remove(user_to_unban)
            await client.send_message(
                chat_id=message.chat.id,
                text=f"✅ Usuario {user_to_unban} desbloqueado correctamente! ✅",
            )
        else:
            await client.send_message(
                chat_id=message.chat.id,
                text=f"🤔 Usuario {user_to_unban} no encontrado en la lista de baneados. 🤔",
            )
    except Exception as e:
        await client.send_message(
            chat_id=message.chat.id, text=f"❌ Error al desbloquear usuario: {e} ❌"
        )


# Comando /broadcast (para administradores)
@app.on_message(filters.command("broadcast") & filters.user(admins))
async def broadcast_handler(client, message: Message):
    try:
        broadcast_message = message.text.split(None, 1)[1]
        for user in users:
            try:
                await client.send_message(chat_id=user, text=broadcast_message)
                await asyncio.sleep(0.1)
            except FloodWait as e:
                await asyncio.sleep(e.x)
            except Exception as e:
                print(f"Error al enviar mensaje a {user}: {e}")
        await client.send_message(
            chat_id=message.chat.id, text="✅ Mensaje enviado a todos los usuarios! ✅"
        )
    except Exception as e:
        await client.send_message(
            chat_id=message.chat.id, text=f"❌ Error al enviar mensaje: {e} ❌"
        )


# Comando /about
@app.on_message(filters.command("about"))
async def about_handler(client, message: Message):
    await client.send_message(
        chat_id=message.chat.id,
        text="Soy un bot de compresión creado por @TheDemonsuprem, versión del bot v2.0 🤖.",
    )


# Comando /clear_user (para administradores)
@app.on_message(filters.command("clear_user") & filters.user(admins))
async def clear_user_handler(client, message: Message):
    try:
        user_to_clear = message.text.split()[1]
        user_folder = create_user_folder(user_to_clear)
        for filename in os.listdir(user_folder):
            file_path = os.path.join(user_folder, filename)
            os.remove(file_path)
        await client.send_message(
            chat_id=message.chat.id,
            text=f"✅ Carpeta de {user_to_clear} eliminada correctamente! ✅",
        )
    except Exception as e:
        await client.send_message(
            chat_id=message.chat.id, text=f"❌ Error al eliminar la carpeta: {e} ❌"
        )


# Comando /clear_all (para administradores)
@app.on_message(filters.command("clear_all") & filters.user(admins))
async def clear_all_handler(client, message: Message):
    try:
        for user_id in os.listdir("./users"):
            user_folder = create_user_folder(user_id)
            for filename in os.listdir(user_folder):
                file_path = os.path.join(user_folder, filename)
                os.remove(file_path)
        await client.send_message(
            chat_id=message.chat.id,
            text="✅ Carpetas de todos los usuarios eliminadas correctamente! ✅",
        )
    except Exception as e:
        await client.send_message(
            chat_id=message.chat.id, text=f"❌ Error al eliminar las carpetas: {e} ❌"
        )


# Ejecutar el bot
if __name__ == "__main__":
    app.run()
