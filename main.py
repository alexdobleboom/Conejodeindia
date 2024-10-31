import os
import time
import asyncio
import ffmpeg
import av
import datetime
import subprocess
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

app = Client("compress_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

current_process = None # Variable para almacenar el proceso actual

# Función para verificar la autorización del usuario (puedes adaptarla a tus necesidades)
def is_user_authorized(username):
    # Aquí debes implementar la lógica de autorización
    # Por ejemplo, puedes usar una lista de usuarios permitidos o un sistema de roles
    authorized_users = ["TheDemonsuprem", "Sasuke286"]
    return username in authorized_users

@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    await app.send_message(chat_id=message.chat.id, text="¡👋 Bienvenido a Armadillo Compress 📚!. Usa el comando /help para ver los comandos disponibles.", reply_markup=get_help_keyboard())

@app.on_message(filters.command("help"))
async def help_command(client, message: Message):
    await app.send_message(chat_id=message.chat.id, text="Estos son los comandos disponibles:\n\n"
                                                        "/compress: Comprime un video.\n"
                                                        "/picarvideo: Divide un video en partes.\n"
                                                        "/max: Cambia el límite del tamaño del video (por ejemplo, /max 5Gb).\n\n"
                                                        "Para usar los comandos, responde a un video con el comando correspondiente.",
                                        reply_markup=get_help_keyboard())

@app.on_message(filters.command("max"))
async def set_max_size(client, message: Message):
    global MAX_VIDEO_SIZE
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
    global original_video_path, current_process
    username = message.from_user.username or f"user_{message.from_user.id}"

    if not is_user_authorized(username):
        #await app.send_message(chat_id=message.chat.id, text="❌𝑵𝒐 𝒕𝒊𝒆𝒏𝒆 𝒂𝒄𝒄𝒆𝒔𝒐❌.")
        return

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

            await client.send_message(chat_id=message.chat.id, text="🚫𝑷𝒓𝒐𝒄𝒆𝒔𝒐 𝒊𝒏𝒊𝒄𝒊𝒂𝒅𝒐 𝒆𝒔𝒑𝒆𝒓𝒆 𝒂 𝒒𝒖𝒆 𝒕𝒆𝒓𝒎𝒊𝒏𝒆🚫.")

            compressed_video_path = f"{os.path.splitext(original_video_path)[0]}_compressed.mkv"
            ffmpeg_command = [
                'ffmpeg', '-y', '-i', original_video_path,
                '-s', '740x480', '-crf', '32', # Ajusta el valor de crf para conseguir una mayor compresión
                '-b:a', '60k', # Reducción de calidad de audio
                '-preset', 'ultrafast', # Opción para optimizar procesamiento
                '-c:v', 'libx265',
                compressed_video_path
            ]

            try:
                start_time = datetime.datetime.now()
                process = subprocess.Popen(ffmpeg_command, stderr=subprocess.PIPE, text=True)
                await app.send_message(chat_id=message.chat.id, text="↗️𝑬𝒏 𝑷𝒓𝒆𝒈𝒓𝒆𝒔𝒐...↘️")

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
                    f"꧁༺ 𝑷𝒓𝒐𝒄𝒆𝒔𝒐 𝑭𝒊𝒏𝒂𝒍𝒊𝒔𝒂𝒅𝒐 ༻꧂\n"
                    f"⏬ 𝑷𝒆𝒔𝒐 𝑶𝒓𝒊𝒈𝒊𝒏𝒂𝒍: {original_size // (1024 * 1024)} MB\n"
                    f"⏫ 𝑷𝒆𝒔𝒐 𝑷𝒓𝒐𝒄𝒆𝒔𝒂𝒅𝒐: {compressed_size // (1024 * 1024)} MB\n"
                    f"▶️ 𝑻𝒊𝒆𝒎𝒑𝒐 𝒅𝒆 𝑷𝒓𝒐𝒄𝒆𝒔𝒂𝒎𝒊𝒆𝒏𝒕𝒐: {processing_time_str}\n"
                    f"🎦 𝑻𝒊𝒆𝒎𝒑𝒐 𝒅𝒆𝒍 𝑽𝒊𝒅𝒆𝒐: {duration_str}\n"
                    f"🎉 ¡𝑸𝒖𝒆 𝒍𝒐 𝒅𝒊𝒔𝒇𝒓𝒖𝒕𝒆!🎊"
                )

                # Enviar el video comprimido con la descripción
                await app.send_document(chat_id=message.chat.id, document=compressed_video_path, caption=description)

            except Exception as e:
                await app.send_message(chat_id=message.chat.id, text=f"⭕𝑶𝒄𝒖𝒓𝒓𝒊𝒐 𝒖𝒏 𝒆𝒓𝒓𝒐𝒓 𝒆𝒏 𝒆𝒍 𝒗𝒊𝒅𝒆𝒐⭕: {e}")
            finally:
                if os.path.exists(original_video_path):
                    os.remove(original_video_path)
                if os.path.exists(compressed_video_path):
                    os.remove(compressed_video_path)
        else:
            await client.send_message(chat_id=message.chat.id, text="El formato de video no es válido. Por favor, envía un video en uno de los siguientes formatos: MP4, MKV, AVI, MOV o WEBM.")
    else:
        await client.send_message(chat_id=message.chat.id, text="‼️𝑹𝒆𝒔𝒑𝒐𝒏𝒅𝒆 𝒂 𝒖𝒏 𝒗𝒊𝒅𝒆𝒐 𝒑𝒂𝒓𝒂 𝒄𝒐𝒎𝒑𝒓𝒊𝒎𝒊𝒓𝒍𝒐‼️.")

@app.on_callback_query()
async def handle_callback_query(client, callback_query):
    global original_video_path, current_process

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
        if current_process is not None:
            current_process.cancel()
            await callback_query.message.edit_text("Proceso cancelado.")
            current_process = None
        return
    elif callback_query.data.endswith("m"):
        interval = int(callback_query.data[:-1]) * 60
    elif callback_query.data.endswith("s"):
        interval = int(callback_query.data[:-1])
    else:
        await callback_query.answer("Opción inválida.", show_alert=True)
        return

    compressed_video_path = f"{os.path.splitext(original_video_path)[0]}_compressed.mkv"

    # Iniciar la compresión en segundo plano con barra de progreso y botón de cancelar
    if callback_query.data == "alta" or callback_query.data == "media" or callback_query.data == "baja" or callback_query.data == "default":
        await callback_query.message.edit_text("Analizando video 📽️...")
        await asyncio.sleep(1) # Simulación de análisis del video
        await callback_query.message.edit_text("Comprimiendo video. Va por 0%", reply_markup=get_cancel_button())

        current_process = asyncio.create_task(compress_video_async(client, callback_query.message, original_video_path, compressed_video_path, compression_settings))

    else:
        await callback_query.message.edit_text("Dividiendo video... Espere.", reply_markup=get_cancel_button())
        current_process = asyncio.create_task(dividir_video_async(client, callback_query.message, original_video_path, interval))



async def compress_video_async(client, message, original_video_path, compressed_video_path, compression_settings):
    global current_process
    try:
        start_time = datetime.datetime.now()
        input_video = ffmpeg.input(original_video_path)
        output_video = (
            input_video
            .output(
                compressed_video_path,
                **compression_settings
            )
            .overwrite_output()
        )
        process = (
            output_video
            .run_async(capture_stderr=True, capture_stdout=True) # Iniciar la compresión en segundo plano
        )

        while True:
            if process.poll() is not None: # Verificar si el proceso ha finalizado
                break

            # Obtener la salida de error y actualizar la barra de progreso
            stderr = process.stderr.read().decode('utf-8')
            progress_info = stderr.split('\n')[-2] # Obtener la última línea de información de progreso
            try:
                progress_percentage = float(progress_info.split(' ')[-2].strip('%')) # Extraer el porcentaje de progreso
            except:
                progress_percentage = 0.0

            # Actualizar la barra de progreso
            try:
                await message.edit_text(
                    text=f"Comprimiendo video. Va por {progress_percentage:.0f}%",
                    reply_markup=get_cancel_button()
                )
            except MessageNotModified:
                pass # Si el mensaje ya fue modificado, ignorar la excepción

            await asyncio.sleep(1) # Esperar 1 segundo antes de actualizar nuevamente

        # Proceso finalizado
        await process.wait()
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

        await client.send_message(chat_id=message.chat.id, text="El video se va a enviar ahora...")
        await client.send_document(chat_id=message.chat.id, document=compressed_video_path, caption=description)

    except Exception as e:
        await client.send_message(chat_id=message.chat.id, text=f"Ocurrió un error en el video: {e}\n\nSalida de error de ffmpeg:\n{ffmpeg.stderr}")
    finally:
        current_process = None # Resetear el proceso actual
        if os.path.exists(original_video_path):
            os.remove(original_video_path)
        if os.path.exists(compressed_video_path):
            os.remove(compressed_video_path)

@app.on_message(filters.command("picarvideo"))
async def picar_video(client, message: Message):
    global original_video_path, current_process
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

async def dividir_video_async(client, message, original_video_path, interval):
    global current_process
    try:
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

            await client.send_document(chat_id=message.chat.id, document=output_path, caption=f"Parte {i} del video.")

            start_time = end_time
            i += 1

        await client.send_message(chat_id=message.chat.id, text="Video dividido correctamente!")

    except Exception as e:
        await client.send_message(chat_id=message.chat.id, text=f"Ocurrió un error al dividir el video: {e}")
    finally:
        current_process = None # Resetear el proceso actual
        if os.path.exists(original_video_path):
            os.remove(original_video_path)

def get_cancel_button():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("Cancelar", callback_data="cancel")]]
    )

def get_help_keyboard():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("Comandos", callback_data="help")]]
    )

app.run()
