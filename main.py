import os
import time
import asyncio
import ffmpeg
import av
import datetime
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import PeerIdInvalid, MessageNotModified

API_ID = 24288670 # Reemplázalo con tu API_ID
API_HASH = "81c58005802498656d6b689dae1edacc" # Reemplázalo con tu API_HASH
BOT_TOKEN = "7507770865:AAFDQ0Lbuo5Ca-mTnqSa-dK_UJENs5B2v1Q" # Reemplázalo con tu token de bot

# Configuraciones del bot
DEFAULT_COMPRESSION_SETTINGS = {
    "resolution": "640x480",
    "crf": "32",
    "audio_bitrate": "60k",
    "fps": "18",
    "preset": "veryfast",
    "codec": "libx264",
}
ALLOWED_FORMATS = ["mp4", "mkv", "avi", "mov", "webm"]
MAX_VIDEO_SIZE = 1024 * 1024 * 1024 # 1 GB por defecto

# Listas de usuarios y administradores (puedes cambiar estas listas)
admins = ["TheDemonsuprem", "TheBigBoss1ro"] # Lista de administradores
users = ["TheDemonsuprem", "Sasuke286"] # Lista de usuarios autorizados

# Directorio base para almacenar las carpetas de los usuarios
BASE_DIR = "users"

# Crea el directorio base si no existe
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)

app = Client("compress_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"
    user_dir = os.path.join(BASE_DIR, username)

    # Crea la carpeta del usuario si no existe
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)

    if username in admins:
        await app.send_message(
            chat_id=message.chat.id,
            text=f"¡👋 Bienvenido, {username}!. Eres un administrador.",
        )
    elif username in users:
        await app.send_message(
            chat_id=message.chat.id,
            text=f"¡👋 Bienvenido, {username}!. Tienes acceso al bot.",
        )
    else:
        await app.send_message(
            chat_id=message.chat.id,
            text="¡👋 Bienvenido! Este bot está restringido. Contacta con un administrador para obtener acceso.",
        )


@app.on_message(filters.command("help"))
async def help_command(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"
    if is_user_authorized(username):
        await app.send_message(
            chat_id=message.chat.id,
            text="Estos son los comandos disponibles:\n\n"
            "/compress: Comprime un video.\n"
            "/picarvideo: Divide un video en partes.\n"
            "/max: Cambia el límite del tamaño del video (por ejemplo, /max 5Gb).\n"
            "/autocompress: Activa la compresión automática.\n\n"
            "Para usar los comandos, responde a un video con el comando correspondiente.",
        )


@app.on_message(filters.command("max"))
async def set_max_size(client, message: Message):
    global MAX_VIDEO_SIZE
    username = message.from_user.username or f"user_{message.from_user.id}"
    if is_user_authorized(username):
        try:
            size_str = message.text.split(" ")[1]
            if size_str.endswith("Gb"):
                size = int(size_str[:-2]) * 1024 * 1024 * 1024
            elif size_str.endswith("Mb"):
                size = int(size_str[:-2]) * 1024 * 1024
            elif size_str.endswith("Kb"):
                size = int(size_str[:-2]) * 1024
            else:
                await client.send_message(
                    chat_id=message.chat.id,
                    text="Formato de tamaño inválido. Usa Gb, Mb o Kb.",
                )
                return
            MAX_VIDEO_SIZE = size
            await client.send_message(
                chat_id=message.chat.id,
                text=f"Límite de tamaño de video actualizado a {size // (1024 * 1024)} MB.",
            )
        except IndexError:
            await client.send_message(
                chat_id=message.chat.id, text="Debes especificar un tamaño válido."
            )


@app.on_message(filters.command("compress"))
async def compress_video(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"
    if is_user_authorized(username):
        if message.reply_to_message and message.reply_to_message.video:
            # Verificar que el video esté en los formatos permitidos
            if message.reply_to_message.video.mime_type.split('/')[1] in ALLOWED_FORMATS:
                # Verificar el tamaño del video
                if message.reply_to_message.video.file_size > MAX_VIDEO_SIZE:
                    await client.send_message(
                        chat_id=message.chat.id,
                        text=f"El video es demasiado grande. El límite actual es de {MAX_VIDEO_SIZE // (1024 * 1024)} MB.",
                    )
                    return

                await client.send_message(
                    chat_id=message.chat.id, text="Descargando video 📹..."
                )
                original_video_path = await app.download_media(
                    message.reply_to_message.video, file_name=os.path.join(BASE_DIR, username)
                )
                original_size = os.path.getsize(original_video_path)

                # Preguntar al usuario qué calidad quiere
                keyboard = InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("Alta Calidad", callback_data="alta")],
                        [InlineKeyboardButton("Media Calidad", callback_data="media")],
                        [InlineKeyboardButton("Baja Calidad", callback_data="baja")],
                        [InlineKeyboardButton("Por Defecto", callback_data="default")],
                    ]
                )
                await client.send_message(
                    chat_id=message.chat.id,
                    text="Elige la calidad de compresión deseada:",
                    reply_markup=keyboard,
                )

            else:
                await client.send_message(
                    chat_id=message.chat.id,
                    text="El formato de video no es válido. Por favor, envía un video en uno de los siguientes formatos: MP4, MKV, AVI, MOV o WEBM.",
                )
        else:
            await client.send_message(
                chat_id=message.chat.id, text="Responde a un video para comprimirlo."
            )


@app.on_message(filters.command("picarvideo"))
async def picar_video(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"
    if is_user_authorized(username):
        if message.reply_to_message and message.reply_to_message.video:
            if message.reply_to_message.video.mime_type.split('/')[1] in ALLOWED_FORMATS:
                # Verificar el tamaño del video
                if message.reply_to_message.video.file_size > MAX_VIDEO_SIZE:
                    await client.send_message(
                        chat_id=message.chat.id,
                        text=f"El video es demasiado grande. El límite actual es de {MAX_VIDEO_SIZE // (1024 * 1024)} MB.",
                    )
                    return

                await client.send_message(
                    chat_id=message.chat.id, text="Descargando video 📹..."
                )
                original_video_path = await app.download_media(
                    message.reply_to_message.video, file_name=os.path.join(BASE_DIR, username)
                )
                original_size = os.path.getsize(original_video_path)

                # Mostrar botones para elegir el tiempo de división
                keyboard = InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("30 Minutos", callback_data="30m")],
                        [InlineKeyboardButton("15 Minutos", callback_data="15m")],
                        [InlineKeyboardButton("5 Minutos", callback_data="5m")],
                        [InlineKeyboardButton("1 Minuto", callback_data="1m")],
                        [InlineKeyboardButton("30 Segundos", callback_data="30s")],
                        [InlineKeyboardButton("15 Segundos", callback_data="15s")],
                        [InlineKeyboardButton("5 Segundos", callback_data="5s")],
                        [InlineKeyboardButton("Cancelar", callback_data="cancel")],
                    ]
                )
                await client.send_message(
                    chat_id=message.chat.id,
                    text="Elige el tiempo para dividir el video:",
                    reply_markup=keyboard,
                )

            else:
                await client.send_message(
                    chat_id=message.chat.id,
                    text="El formato de video no es válido. Por favor, envía un video en uno de los siguientes formatos: MP4, MKV, AVI, MOV o WEBM.",
                )
        else:
            await client.send_message(
                chat_id=message.chat.id, text="Responde a un video para dividirlo."
            )


@app.on_message(filters.command("autocompress"))
async def autocompress_video(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"
    if is_user_authorized(username):
        if message.reply_to_message and message.reply_to_message.video:
            # Verificar que el video esté en los formatos permitidos
            if message.reply_to_message.video.mime_type.split('/')[1] in ALLOWED_FORMATS:
                # Verificar el tamaño del video
                if message.reply_to_message.video.file_size > MAX_VIDEO_SIZE:
                    await client.send_message(
                        chat_id=message.chat.id,
                        text=f"El video es demasiado grande. El límite actual es de {MAX_VIDEO_SIZE // (1024 * 1024)} MB.",
                    )
                    return

                await client.send_message(
                    chat_id=message.chat.id, text="Descargando video 📹..."
                )
                original_video_path = await app.download_media(
                    message.reply_to_message.video, file_name=os.path.join(BASE_DIR, username)
                )
                original_size = os.path.getsize(original_video_path)

                await client.send_message(
                    chat_id=message.chat.id, text="Comprimiendo video..."
                )

                compressed_video_path = f"{os.path.splitext(original_video_path)[0]}_compressed.mkv"
                input_video = ffmpeg.input(original_video_path)
                output_video = (
                    input_video
                    .output(
                        compressed_video_path,
                        **DEFAULT_COMPRESSION_SETTINGS
                    )
                    .overwrite_output()
                )
                process = output_video.run(capture_stderr=True, capture_stdout=True)

                while True:
                    if process.poll() is not None:
                        break
                    stderr = process.stderr.read().decode('utf-8')
                    progress_info = stderr.split('\n')[-2]
                    try:
                        progress_percentage = float(
                            progress_info.split(' ')[-2].strip('%')
                        )
                    except:
                        progress_percentage = 0.0

                    #await client.send_message(chat_id=message.chat.id, text=f"Comprimiendo video. Va por {progress_percentage:.0f}%")
                    await asyncio.sleep(1)

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

                await client.send_message(
                    chat_id=message.chat.id, text="El video se va a enviar ahora..."
                )
                await client.send_document(
                    chat_id=message.chat.id,
                    document=compressed_video_path,
                    caption=description,
                )

                os.remove(original_video_path)
                os.remove(compressed_video_path)

            else:
                await client.send_message(
                    chat_id=message.chat.id,
                    text="El formato de video no es válido. Por favor, envía un video en uno de los siguientes formatos: MP4, MKV, AVI, MOV o WEBM.",
                )
        else:
            await client.send_message(
                chat_id=message.chat.id, text="Responde a un video para comprimirlo."
            )


@app.on_callback_query()
async def handle_callback_query(client, callback_query):
    global original_video_path
    username = callback_query.from_user.username or f"user_{callback_query.from_user.id}"
    if is_user_authorized(username):
        if callback_query.data == "alta":
            compression_settings = {
                "resolution": "1920x1080",
                "crf": "20", # Valor más bajo para mayor calidad
                "audio_bitrate": "128k",
                "fps": "24",
                "preset": "medium", # Balance entre calidad y velocidad
                "codec": "libx265",
            }
        elif callback_query.data == "media":
            compression_settings = {
                "resolution": "1280x720",
                "crf": "23",
                "audio_bitrate": "96k",
                "fps": "24",
                "preset": "medium",
                "codec": "libx265",
            }
        elif callback_query.data == "baja":
            compression_settings = {
                "resolution": "740x480",
                "crf": "28",
                "audio_bitrate": "60k",
                "fps": "24",
                "preset": "fast", # Prioriza velocidad sobre calidad
                "codec": "libx264",
            }
        elif callback_query.data == "default":
            compression_settings = DEFAULT_COMPRESSION_SETTINGS
        elif callback_query.data == "cancel":
            await callback_query.message.edit_text("Proceso cancelado.")
            return
        elif callback_query.data.endswith("m"):
            interval = int(callback_query.data[:-1]) * 60
        elif callback_query.data.endswith("s"):
            interval = int(callback_query.data[:-1])
        else:
            await callback_query.answer("Opción inválida.", show_alert=True)
            return

        compressed_video_path = f"{os.path.splitext(original_video_path)[0]}_compressed.mkv"

        # Iniciar la compresión en segundo plano
        if (
            callback_query.data == "alta"
            or callback_query.data == "media"
            or callback_query.data == "baja"
            or callback_query.data == "default"
        ):
            await callback_query.message.edit_text("Comprimiendo video...")

            input_video = ffmpeg.input(original_video_path)
            output_video = (
                input_video
                .output(
                    compressed_video_path, **compression_settings
                )
                .overwrite_output()
            )
            process = output_video.run(capture_stderr=True, capture_stdout=True)

            while True:
                if process.poll() is not None:
                    break
                stderr = process.stderr.read().decode('utf-8')
                progress_info = stderr.split('\n')[-2]
                try:
                    progress_percentage = float(
                        progress_info.split(' ')[-2].strip('%')
                    )
                except:
                    progress_percentage = 0.0

                #await client.send_message(chat_id=message.chat.id, text=f"Comprimiendo video. Va por {progress_percentage:.0f}%")
                await asyncio.sleep(1)

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

            await client.send_message(
                chat_id=callback_query.message.chat.id,
                text="El video se va a enviar ahora...",
            )
            await client.send_document(
                chat_id=callback_query.message.chat.id,
                document=compressed_video_path,
                caption=description,
            )

            os.remove(original_video_path)
            os.remove(compressed_video_path)

        else:
            await callback_query.message.edit_text("Dividiendo video...")

            # Obtener información del video
            video_info = ffmpeg.probe(original_video_path)
            duration = float(video_info['format']['duration'])

            # Dividir el video
            i = 1
            start_time = 0
            while start_time < duration:
                end_time = min(start_time + interval, duration)
                output_path = f"{os.path.splitext(original_video_path)[0]}_parte_{i}.mkv"
                input_video = ffmpeg.input(original_video_path, ss=start_time, to=end_time)
                output_video = (
                    input_video
                    .output(output_path)
                    .overwrite_output()
                )
                ffmpeg.run(output_video)

                await client.send_document(
                    chat_id=callback_query.message.chat.id,
                    document=output_path,
                    caption=f"Parte {i} del video.",
                )

                start_time = end_time
                i += 1

            await client.send_message(
                chat_id=callback_query.message.chat.id,
                text="Video dividido correctamente!",
            )

            os.remove(original_video_path)


@app.on_message(filters.command("add"))
async def add_user(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"
    if username in admins:
        try:
            new_user = message.text.split(" ")[1].replace("@", "")
            users.append(new_user)
            await client.send_message(
                chat_id=message.chat.id,
                text=f"Usuario @{new_user} agregado correctamente.",
            )
        except IndexError:
            await client.send_message(
                chat_id=message.chat.id,
                text="Debes proporcionar el nombre de usuario del nuevo usuario.",
            )


@app.on_message(filters.command("ban"))
async def ban_user(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"
    if username in admins:
        try:
            user_to_ban = message.text.split(" ")[1].replace("@", "")
            if user_to_ban in users:
                users.remove(user_to_ban)
                await client.send_message(
                    chat_id=message.chat.id,
                    text=f"Usuario @{user_to_ban} baneado correctamente.",
                )
            else:
                await client.send_message(
                    chat_id=message.chat.id,
                    text=f"El usuario @{user_to_ban} no está en la lista de usuarios.",
                )
        except IndexError:
            await client.send_message(
                chat_id=message.chat.id,
                text="Debes proporcionar el nombre de usuario del usuario a banear.",
            )


@app.on_message(filters.command("listuser"))
async def list_users(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"
    if username in admins:
        if users:
            user_list = "\n".join(f"@{user}" for user in users)
            await client.send_message(
                chat_id=message.chat.id, text=f"Usuarios:\n{user_list}"
            )
        else:
            await client.send_message(chat_id=message.chat.id, text="No hay usuarios.")


@app.on_message(filters.command("listadmin"))
async def list_admins(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"
    if username in admins:
        if admins:
            admin_list = "\n".join(f"@{admin}" for admin in admins)
            await client.send_message(
                chat_id=message.chat.id, text=f"Administradores:\n{admin_list}"
            )
        else:
            await client.send_message(
                chat_id=message.chat.id, text="No hay administradores."
            )


@app.on_message(filters.command("ls"))
async def list_folders(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"
    if is_user_authorized(username):
        user_folders = [
            f for f in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, f))
        ]
        if user_folders:
            folder_list = "\n".join(
                f"• {folder}: {get_folder_size(os.path.join(BASE_DIR, folder))} GB"
                for folder in user_folders
            )
            await client.send_message(
                chat_id=message.chat.id, text=f"Carpetas:\n{folder_list}"
            )
        else:
            await client.send_message(chat_id=message.chat.id, text="No hay carpetas.")


@app.on_message(filters.command("maxls"))
async def set_max_folder_size(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"
    if username in admins:
        try:
            target_user = message.text.split(" ")[1].replace("@", "")
            size_str = message.text.split(" ")[2]
            if size_str.endswith("Gb"):
                size = int(size_str[:-2]) * 1024 * 1024 * 1024
            elif size_str.endswith("Mb"):
                size = int(size_str[:-2]) * 1024 * 1024
            elif size_str.endswith("Kb"):
                size = int(size_str[:-2]) * 1024
            else:
                await client.send_message(
                    chat_id=message.chat.id,
                    text="Formato de tamaño inválido. Usa Gb, Mb o Kb.",
                )
                return
            set_folder_size(target_user, size)
            await client.send_message(
                chat_id=message.chat.id,
                text=f"Tamaño máximo de carpeta para @{target_user} actualizado a {size // (1024 * 1024)} MB.",
            )
        except IndexError:
            await client.send_message(
                chat_id=message.chat.id,
                text="Debes proporcionar el nombre de usuario y el nuevo tamaño máximo de la carpeta.",
            )


def get_folder_size(folder_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return round(total_size / (1024 * 1024 * 1024), 2)


def set_folder_size(username, size):
    user_dir = os.path.join(BASE_DIR, username)
    if os.path.exists(user_dir):
        # Eliminar la carpeta del usuario si el tamaño es 0
        if size == 0:
            os.rmdir(user_dir)
        else:
            # Actualizar el tamaño máximo de la carpeta
            # Puedes usar una variable global o un diccionario para guardar el tamaño máximo
            # por usuario
            pass # Implementa la lógica de actualización de tamaño aquí


def is_user_authorized(username):
    return username in admins or username in users


@app.on_message(filters.video)
async def handle_video_message(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"
    if is_user_authorized(username):
        user_dir = os.path.join(BASE_DIR, username)
        # Verificar el tamaño de la carpeta del usuario
        if get_folder_size(user_dir) >= 2:
            await client.send_message(
                chat_id=message.chat.id,
                text="Has superado el límite de almacenamiento de 2 GB. No puedes enviar más videos.",
            )
            # Banear al usuario del bot
            if username in users:
                users.remove(username)
            return

        await client.send_message(chat_id=message.chat.id, text="Comprimiendo video...")
        original_video_path = await app.download_media(
            message.video, file_name=user_dir
        )
        original_size = os.path.getsize(original_video_path)

        compressed_video_path = f"{os.path.splitext(original_video_path)[0]}_compressed.mkv"
        input_video = ffmpeg.input(original_video_path)
        output_video = (
            input_video
            .output(
                compressed_video_path, **DEFAULT_COMPRESSION_SETTINGS
            )
            .overwrite_output()
        )
        process = output_video.run(capture_stderr=True, capture_stdout=True)

        while True:
            if process.poll() is not None:
                break
            stderr = process.stderr.read().decode('utf-8')
            progress_info = stderr.split('\n')[-2]
            try:
                progress_percentage = float(
                    progress_info.split(' ')[-2].strip('%')
                )
            except:
                progress_percentage = 0.0

            #await client.send_message(chat_id=message.chat.id, text=f"Comprimiendo video. Va por {progress_percentage:.0f}%")
            await asyncio.sleep(1)

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

        await client.send_message(
            chat_id=message.chat.id, text="El video se va a enviar ahora..."
        )
        await client.send_document(
            chat_id=message.chat.id,
            document=compressed_video_path,
            caption=description,
        )

        os.remove(original_video_path)
        os.remove(compressed_video_path)


app.run()
