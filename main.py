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
    "codec": "libx264"
}
ALLOWED_FORMATS = ["mp4", "mkv", "avi", "mov", "webm"]
MAX_VIDEO_SIZE = 1024 * 1024 * 1024 # 1 GB por defecto

# Listas de usuarios y administradores (puedes cambiar estas listas)
admins = ["TheDemonsuprem", "Sasuke286"] # Lista de administradores
users = ["TheDemonsuprem", "Sasuke286"] # Lista de usuarios autorizados

app = Client("compress_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"
    if username in admins:
        await app.send_message(chat_id=message.chat.id, text=f"¡👋 Bienvenido, {username}!. Eres un administrador.")
    elif username in users:
        await app.send_message(chat_id=message.chat.id, text=f"¡👋 Bienvenido, {username}!. Tienes acceso al bot.")
    else:
        await app.send_message(chat_id=message.chat.id, text="¡👋 Bienvenido! Este bot está restringido. Contacta con un administrador para obtener acceso.")

@app.on_message(filters.command("help"))
async def help_command(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"
    if is_user_authorized(username):
        await app.send_message(chat_id=message.chat.id, text="Estos son los comandos disponibles:\n\n"
                                                            "/compress: Comprime un video.\n"
                                                            "/picarvideo: Divide un video en partes.\n"
                                                            "/max: Cambia el límite del tamaño del video (por ejemplo, /max 5Gb).\n\n"
                                                            "Para usar los comandos, responde a un video con el comando correspondiente.")

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
                await client.send_message(chat_id=message.chat.id, text="Formato de tamaño inválido. Usa Gb, Mb o Kb.")
                return
            MAX_VIDEO_SIZE = size
            await client.send_message(chat_id=message.chat.id, text=f"Límite de tamaño de video actualizado a {size // (1024 * 1024)} MB.")
        except IndexError:
            await client.send_message(chat_id=message.chat.id, text="Debes especificar un tamaño válido.")

@app.on_message(filters.command("compress"))
async def compress_video(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"
    if is_user_authorized(username):
        if message.reply_to_message and message.reply_to_message.video:
            # Verificar que el video esté en los formatos permitidos
            if message.reply_to_message.video.mime_type.split('/')[1] in ALLOWED_FORMATS:
                # Verificar el tamaño del video
                if message.reply_to_message.video.file_size > MAX_VIDEO_SIZE:
                    await client.send_message(chat_id=message.chat.id, text=f"El video es demasiado grande. El límite actual es de {MAX_VIDEO_SIZE // (1024 * 1024)} MB.")
                    return

                await client.send_message(chat_id=message.chat.id, text="Descargando video 📹...")
                original_video_path = await app.download_media(message.reply_to_message.video)
                original_size = os.path.getsize(original_video_path)

                # Preguntar al usuario qué calidad quiere
                keyboard = InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("Alta Calidad", callback_data="alta")],
                        [InlineKeyboardButton("Media Calidad", callback_data="media")],
                        [InlineKeyboardButton("Baja Calidad", callback_data="baja")],
                        [InlineKeyboardButton("Por Defecto", callback_data="default")]
                    ]
                )
                await client.send_message(chat_id=message.chat.id, text="Elige la calidad de compresión deseada:", reply_markup=keyboard)

            else:
                await client.send_message(chat_id=message.chat.id, text="El formato de video no es válido. Por favor, envía un video en uno de los siguientes formatos: MP4, MKV, AVI, MOV o WEBM.")
        else:
            await client.send_message(chat_id=message.chat.id, text="Responde a un video para comprimirlo.")

@app.on_message(filters.command("picarvideo"))
async def picar_video(client, message: Message):
    username = message.from_user.username or f"user_{message.from_user.id}"
    if is_user_authorized(username):
        if message.reply_to_message and message.reply_to_message.video:
            if message.reply_to_message.video.mime_type.split('/')[1] in ALLOWED_FORMATS:
                # Verificar el tamaño del video
                if message.reply_to_message.video.file_size > MAX_VIDEO_SIZE:
                    await client.send_message(chat_id=message.chat.id, text=f"El video es demasiado grande. El límite actual es de {MAX_VIDEO_SIZE // (1024 * 1024)} MB.")
                    return

                await client.send_message(chat_id=message.chat.id, text="Descargando video 📹...")
                original_video_path = await app.download_media(message.reply_to_message.video)
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
                        [InlineKeyboardButton("Cancelar", callback_data="cancel")]
                    ]
                )
                await client.send_message(chat_id=message.chat.id, text="Elige el tiempo para dividir el video:", reply_markup=keyboard)

            else:
                await client.send_message(chat_id=message.chat.id, text="El formato de video no es válido. Por favor, envía un video en uno de los siguientes formatos: MP4, MKV, AVI, MOV o WEBM.")
        else:
            await client.send_message(chat_id=message.chat.id, text="Responde a un video para dividirlo.")

@app.on_callback_query()
async def handle_callback_query(client, callback_query):
    global original_video_path
    if callback_query.data == "alta":
        compression_settings = {
            "resolution": "1920x1080",
            "crf": "20", # Valor más bajo para mayor calidad
            "audio_bitrate": "128k",
            "fps": "24",
            "preset": "medium", # Balance entre calidad y velocidad
            "codec": "libx265"
        }
    elif callback_query.data == "media":
        compression_settings = {
            "resolution": "1280x720",
            "crf": "23",
            "audio_bitrate": "96k",
            "fps": "24",
            "preset": "medium",
            "codec": "libx265"
        }
    elif callback_query.data == "baja":
        compression_settings = {
            "resolution": "740x480",
            "crf": "28",
            "audio_bitrate": "60k",
            "fps": "24",
            "preset": "fast", # Prioriza velocidad sobre calidad
            "codec": "libx264"
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
    if callback_query.data == "alta" or callback_query.data == "media" or callback_query.data == "baja" or callback_query.data == "default":
        await callback_query.message.edit_text("Comprimiendo video...")

        input_video = ffmpeg.input(original_video_path)
        output_video = (
            input_video
            .output(
                compressed_video_path,
                **compression_settings
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
                progress_percentage = float(progress_info.split(' ')[-2].strip('%'))
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

        await client.send_message(chat_id=callback_query.message.chat.id, text="El video se va a enviar ahora...")
        await client.send_document(chat_id=callback_query.message.chat.id, document=compressed_video_path, caption=description)

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

            await client.send_document(chat_id=callback_query.message.chat.id, document=output_path, caption=f"Parte {i} del video.")

            start_time = end_time
            i += 1

        await client.send_message(chat_id=callback_query.message.chat.id, text="Video dividido correctamente!")

        os.remove(original_video_path)

def is_user_authorized(username):
    return username in admins or username in users

app.run()
